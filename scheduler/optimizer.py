"""
Core scheduling optimizer using Google OR-Tools CP-SAT solver.
"""

try:
    from ortools.sat.python import cp_model
except ImportError:
    from ortools.sat import cp_model
from typing import List, Dict, Tuple, Optional
from .models import (
    Scenario, Schedule, BusSchedule, ChargingStop, 
    StationChargingEvent, Bus, Station
)
from .utils import (
    calculate_travel_time, get_cumulative_distances,
    validate_battery_range
)
import itertools


class ChargingScheduler:
    """
    Constraint programming based scheduler for electric bus charging.
    Uses Google OR-Tools CP-SAT solver.
    """
    
    def __init__(self, time_limit_seconds: int = 300):
        """
        Initialize the scheduler.
        
        Args:
            time_limit_seconds: Maximum time to spend solving (default 5 minutes)
        """
        self.time_limit_seconds = time_limit_seconds
    
    def build_schedule(self, scenario: Scenario) -> Schedule:
        """
        Build an optimized charging schedule for all buses in the scenario.
        
        Args:
            scenario: The scenario to schedule
            
        Returns:
            Complete schedule with charging plans for all buses
        """
        model = cp_model.CpModel()
        
        # Create variables for each bus
        bus_vars = self._create_bus_variables(model, scenario)
        
        # Add hard constraints
        self._add_battery_constraints(model, bus_vars, scenario)
        self._add_charger_capacity_constraints(model, bus_vars, scenario)
        self._add_time_ordering_constraints(model, bus_vars, scenario)
        
        # Build objective function
        objective = self._build_objective(model, bus_vars, scenario)
        model.Minimize(objective)
        
        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_seconds
        solver.parameters.log_search_progress = False
        
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_solution(solver, bus_vars, scenario)
        else:
            # Return a greedy fallback solution
            return self._greedy_fallback(scenario)
    
    def _create_bus_variables(self, model: cp_model.CpModel, scenario: Scenario) -> Dict:
        """Create decision variables for each bus."""
        bus_vars = {}
        max_time = 24 * 60  # 24 hours in minutes
        
        for bus in scenario.buses:
            stations = scenario.route.stations
            bus_vars[bus.id] = {
                'uses_station': [],  # Boolean: does bus charge at this station?
                'arrival_time': [],  # When bus arrives at station
                'charge_start': [],  # When charging starts
                'charge_end': [],    # When charging ends
                'wait_time': [],     # Wait time at station
                'departure_from_station': [],  # When bus leaves station
            }
            
            for i, station in enumerate(stations):
                # Boolean: does this bus use this station?
                uses = model.NewBoolVar(f'{bus.id}_uses_{station.id}')
                bus_vars[bus.id]['uses_station'].append(uses)
                
                # Time variables (only meaningful if uses_station is True)
                arrival = model.NewIntVar(0, max_time, f'{bus.id}_arrival_{station.id}')
                charge_start = model.NewIntVar(0, max_time, f'{bus.id}_charge_start_{station.id}')
                charge_end = model.NewIntVar(0, max_time, f'{bus.id}_charge_end_{station.id}')
                wait = model.NewIntVar(0, max_time, f'{bus.id}_wait_{station.id}')
                departure = model.NewIntVar(0, max_time, f'{bus.id}_depart_{station.id}')
                
                bus_vars[bus.id]['arrival_time'].append(arrival)
                bus_vars[bus.id]['charge_start'].append(charge_start)
                bus_vars[bus.id]['charge_end'].append(charge_end)
                bus_vars[bus.id]['wait_time'].append(wait)
                bus_vars[bus.id]['departure_from_station'].append(departure)
                
                # If using station: charge_end = charge_start + charging_time
                model.Add(charge_end == charge_start + station.charging_time_min).OnlyEnforceIf(uses)
                
                # If using station: wait = charge_start - arrival
                model.Add(wait == charge_start - arrival).OnlyEnforceIf(uses)
                
                # If using station: departure = charge_end
                model.Add(departure == charge_end).OnlyEnforceIf(uses)
                
                # If not using station: all times are 0
                model.Add(wait == 0).OnlyEnforceIf(uses.Not())
        
        return bus_vars
    
    def _add_battery_constraints(self, model: cp_model.CpModel, bus_vars: Dict, scenario: Scenario):
        """Ensure buses don't run out of battery between charges."""
        for bus in scenario.buses:
            # Get stations in order for this bus's direction
            if bus.is_forward_direction():
                stations = scenario.route.stations
                start_point = "Bengaluru"
                end_point = "Kochi"
            else:
                stations = list(reversed(scenario.route.stations))
                start_point = "Kochi"
                end_point = "Bengaluru"
            
            # Get cumulative distances
            distances = get_cumulative_distances(scenario.route, bus.direction)
            
            # Must charge at least minimum number of times
            total_distance = scenario.route.get_total_distance()
            min_charges = int(total_distance / scenario.route.battery_range_km)
            if total_distance % scenario.route.battery_range_km > 0:
                min_charges += 1
            min_charges = max(0, min_charges - 1)  # -1 because we start with full battery
            
            # Ensure minimum charges
            total_uses = sum(bus_vars[bus.id]['uses_station'])
            model.Add(total_uses >= min_charges)
            
            # Ensure we can reach first charging station
            if stations:
                first_station_dist = distances.get(stations[0].id, 0)
                if first_station_dist > scenario.route.battery_range_km:
                    # Must charge at first station
                    model.Add(bus_vars[bus.id]['uses_station'][0] == 1)
    
    def _add_charger_capacity_constraints(self, model: cp_model.CpModel, bus_vars: Dict, scenario: Scenario):
        """Ensure no more than 'chargers' buses use a station simultaneously."""
        for station_idx, station in enumerate(scenario.route.stations):
            # Get all buses that might use this station
            charging_intervals = []
            
            for bus in scenario.buses:
                uses = bus_vars[bus.id]['uses_station'][station_idx]
                start = bus_vars[bus.id]['charge_start'][station_idx]
                end = bus_vars[bus.id]['charge_end'][station_idx]
                
                charging_intervals.append((bus.id, uses, start, end))
            
            # For each pair of buses, if both use this station, they can't overlap
            for i, (bus1_id, uses1, start1, end1) in enumerate(charging_intervals):
                for j, (bus2_id, uses2, start2, end2) in enumerate(charging_intervals):
                    if i >= j:
                        continue
                    
                    # If both buses use this station, they must not overlap
                    both_use = model.NewBoolVar(f'both_use_{station.id}_{bus1_id}_{bus2_id}')
                    model.AddMultiplicationEquality(both_use, [uses1, uses2])
                    
                    # If both use, then either bus1 finishes before bus2 starts, or vice versa
                    bus1_first = model.NewBoolVar(f'{bus1_id}_before_{bus2_id}_{station.id}')
                    
                    # If both use and bus1 first: end1 <= start2
                    model.Add(end1 <= start2).OnlyEnforceIf([both_use, bus1_first])
                    
                    # If both use and bus2 first: end2 <= start1
                    model.Add(end2 <= start1).OnlyEnforceIf([both_use, bus1_first.Not()])
    
    def _add_time_ordering_constraints(self, model: cp_model.CpModel, bus_vars: Dict, scenario: Scenario):
        """Ensure buses arrive at stations in correct time order based on travel."""
        for bus in scenario.buses:
            departure_time = bus.get_departure_minutes()
            
            # Get stations and distances for this direction
            if bus.is_forward_direction():
                stations = scenario.route.stations
                start_point = "Bengaluru"
            else:
                stations = list(reversed(scenario.route.stations))
                start_point = "Kochi"
            
            distances = get_cumulative_distances(scenario.route, bus.direction)
            
            # Track current time and position
            prev_time = departure_time
            prev_distance = 0.0
            
            for station_idx, station in enumerate(stations):
                station_distance = distances.get(station.id, 0)
                segment_distance = station_distance - prev_distance
                travel_time = calculate_travel_time(segment_distance, scenario.route.speed_kmh)
                
                uses = bus_vars[bus.id]['uses_station'][station_idx]
                arrival = bus_vars[bus.id]['arrival_time'][station_idx]
                departure = bus_vars[bus.id]['departure_from_station'][station_idx]
                
                # If using this station: arrival >= prev_time + travel_time
                model.Add(arrival >= prev_time + travel_time).OnlyEnforceIf(uses)
                
                # Update for next iteration
                # If we use this station, next segment starts from departure time
                # This is handled by tracking the last used station
                prev_distance = station_distance
                
                # For next station, prev_time should be departure from this station if used
                # We'll use a more sophisticated approach: track last departure
                if station_idx == 0:
                    # First station: prev_time is departure time
                    model.Add(departure >= departure_time + travel_time).OnlyEnforceIf(uses)
                else:
                    # Later stations: must arrive after previous station's departure (if used)
                    prev_uses = bus_vars[bus.id]['uses_station'][station_idx - 1]
                    prev_departure = bus_vars[bus.id]['departure_from_station'][station_idx - 1]
                    
                    # If both this and previous station are used
                    both_used = model.NewBoolVar(f'{bus.id}_both_{station_idx}')
                    model.AddMultiplicationEquality(both_used, [uses, prev_uses])
                    
                    # Calculate travel time from previous station
                    prev_station = stations[station_idx - 1]
                    prev_station_dist = distances.get(prev_station.id, 0)
                    inter_station_dist = station_distance - prev_station_dist
                    inter_travel_time = calculate_travel_time(inter_station_dist, scenario.route.speed_kmh)
                    
                    model.Add(arrival >= prev_departure + inter_travel_time).OnlyEnforceIf(both_used)
    
    def _build_objective(self, model: cp_model.CpModel, bus_vars: Dict, scenario: Scenario) -> cp_model.LinearExpr:
        """Build the objective function based on weights."""
        # Calculate total wait time for each bus
        bus_total_waits = {}
        for bus in scenario.buses:
            total_wait = sum(bus_vars[bus.id]['wait_time'])
            bus_total_waits[bus.id] = total_wait
        
        # Individual: max wait time across all buses
        max_individual_wait = model.NewIntVar(0, 24 * 60, 'max_individual_wait')
        for bus_id, wait in bus_total_waits.items():
            model.Add(max_individual_wait >= wait)
        
        # Operator: max total wait time for any operator
        operator_waits = {}
        for operator in scenario.get_all_operators():
            operator_buses = scenario.get_buses_by_operator(operator)
            operator_total = sum(bus_total_waits[bus.id] for bus in operator_buses)
            operator_waits[operator] = operator_total
        
        max_operator_wait = model.NewIntVar(0, 24 * 60 * 20, 'max_operator_wait')
        for operator, wait in operator_waits.items():
            model.Add(max_operator_wait >= wait)
        
        # Overall: total wait time across all buses
        total_wait = sum(bus_total_waits.values())
        
        # Weighted objective
        weights = scenario.weights
        objective = (
            int(weights.individual * 100) * max_individual_wait +
            int(weights.operator * 10) * max_operator_wait +
            int(weights.overall * 1) * total_wait
        )
        
        return objective
    
    def _extract_solution(self, solver: cp_model.CpSolver, bus_vars: Dict, scenario: Scenario) -> Schedule:
        """Extract the solution from the solver."""
        bus_schedules = []
        station_schedules = {station.id: [] for station in scenario.route.stations}
        
        for bus in scenario.buses:
            charging_stops = []
            total_wait = 0
            
            # Get stations in order for this direction
            if bus.is_forward_direction():
                stations = scenario.route.stations
            else:
                stations = list(reversed(scenario.route.stations))
            
            # Extract charging stops
            for station_idx, station in enumerate(stations):
                uses = solver.Value(bus_vars[bus.id]['uses_station'][station_idx])
                
                if uses:
                    arrival = solver.Value(bus_vars[bus.id]['arrival_time'][station_idx])
                    charge_start = solver.Value(bus_vars[bus.id]['charge_start'][station_idx])
                    charge_end = solver.Value(bus_vars[bus.id]['charge_end'][station_idx])
                    wait = solver.Value(bus_vars[bus.id]['wait_time'][station_idx])
                    
                    charging_stops.append(ChargingStop(
                        station_id=station.id,
                        arrival_time_min=arrival,
                        charge_start_time_min=charge_start,
                        charge_end_time_min=charge_end,
                        wait_time_min=wait
                    ))
                    
                    total_wait += wait
                    
                    # Add to station schedule
                    station_schedules[station.id].append(StationChargingEvent(
                        bus_id=bus.id,
                        operator=bus.operator,
                        start_time_min=charge_start,
                        end_time_min=charge_end
                    ))
            
            # Calculate arrival time at destination
            departure_min = bus.get_departure_minutes()
            total_distance = scenario.route.get_total_distance()
            base_travel_time = calculate_travel_time(total_distance, scenario.route.speed_kmh)
            total_charging_time = sum(stop.charge_end_time_min - stop.charge_start_time_min 
                                     for stop in charging_stops)
            
            arrival_time_min = departure_min + base_travel_time + total_charging_time + total_wait
            
            bus_schedules.append(BusSchedule(
                bus_id=bus.id,
                operator=bus.operator,
                direction=bus.direction,
                departure_time=bus.departure_time,
                arrival_time_min=arrival_time_min,
                total_travel_time_min=base_travel_time + total_charging_time,
                total_wait_time_min=total_wait,
                charging_stops=charging_stops
            ))
        
        # Sort station schedules by start time
        for station_id in station_schedules:
            station_schedules[station_id].sort(key=lambda x: x.start_time_min)
        
        return Schedule(
            scenario_id=scenario.id,
            bus_schedules=bus_schedules,
            station_schedules=station_schedules
        )
    
    def _greedy_fallback(self, scenario: Scenario) -> Schedule:
        """
        Greedy fallback solution if CP-SAT fails.
        Simple first-come-first-served approach.
        """
        bus_schedules = []
        station_schedules = {station.id: [] for station in scenario.route.stations}
        station_next_available = {station.id: 0 for station in scenario.route.stations}
        
        for bus in scenario.buses:
            charging_stops = []
            total_wait = 0
            
            # Determine which stations to use (simple: charge every ~200km)
            if bus.is_forward_direction():
                stations = scenario.route.stations
                # Use stations A and C (or B and D)
                stations_to_use = [stations[0], stations[2]] if len(stations) >= 3 else stations[:2]
            else:
                stations = list(reversed(scenario.route.stations))
                stations_to_use = [stations[0], stations[2]] if len(stations) >= 3 else stations[:2]
            
            distances = get_cumulative_distances(scenario.route, bus.direction)
            departure_min = bus.get_departure_minutes()
            current_time = departure_min
            
            for station in stations_to_use:
                # Calculate arrival time
                station_distance = distances.get(station.id, 0)
                travel_time = calculate_travel_time(station_distance, scenario.route.speed_kmh)
                arrival_time = departure_min + travel_time
                
                # Check if station is available
                charge_start = max(arrival_time, station_next_available[station.id])
                wait_time = charge_start - arrival_time
                charge_end = charge_start + station.charging_time_min
                
                charging_stops.append(ChargingStop(
                    station_id=station.id,
                    arrival_time_min=arrival_time,
                    charge_start_time_min=charge_start,
                    charge_end_time_min=charge_end,
                    wait_time_min=wait_time
                ))
                
                total_wait += wait_time
                station_next_available[station.id] = charge_end
                
                station_schedules[station.id].append(StationChargingEvent(
                    bus_id=bus.id,
                    operator=bus.operator,
                    start_time_min=charge_start,
                    end_time_min=charge_end
                ))
                
                current_time = charge_end
            
            # Calculate final arrival
            total_distance = scenario.route.get_total_distance()
            base_travel_time = calculate_travel_time(total_distance, scenario.route.speed_kmh)
            total_charging_time = len(charging_stops) * scenario.route.stations[0].charging_time_min
            arrival_time_min = departure_min + base_travel_time + total_charging_time + total_wait
            
            bus_schedules.append(BusSchedule(
                bus_id=bus.id,
                operator=bus.operator,
                direction=bus.direction,
                departure_time=bus.departure_time,
                arrival_time_min=arrival_time_min,
                total_travel_time_min=base_travel_time + total_charging_time,
                total_wait_time_min=total_wait,
                charging_stops=charging_stops
            ))
        
        return Schedule(
            scenario_id=scenario.id,
            bus_schedules=bus_schedules,
            station_schedules=station_schedules
        )
