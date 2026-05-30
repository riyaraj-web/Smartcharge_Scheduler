"""
Data models for the bus charging scheduler.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, time


@dataclass
class Station:
    """Represents a charging station along the route."""
    id: str
    chargers: int = 1
    charging_time_min: int = 25
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class RouteSegment:
    """Represents a segment of the route between two points."""
    from_point: str
    to_point: str
    distance_km: float


@dataclass
class Route:
    """Represents the complete route with stations."""
    name: str
    segments: List[RouteSegment]
    stations: List[Station]
    battery_range_km: float = 240.0
    speed_kmh: float = 60.0
    
    def get_distance_to_station(self, station_id: str, from_start: str = "Bengaluru") -> float:
        """Calculate cumulative distance from start to a station."""
        distance = 0.0
        for segment in self.segments:
            if segment.from_point == from_start or distance > 0:
                distance += segment.distance_km
                if segment.to_point == station_id:
                    return distance
        return distance
    
    def get_station_by_id(self, station_id: str) -> Optional[Station]:
        """Get station by ID."""
        for station in self.stations:
            if station.id == station_id:
                return station
        return None
    
    def get_total_distance(self) -> float:
        """Get total route distance."""
        return sum(seg.distance_km for seg in self.segments)


@dataclass
class Weights:
    """Optimization weights for the scheduler."""
    individual: float = 1.0  # Minimize max delay for any single bus
    operator: float = 1.0    # Minimize max delay for any operator
    overall: float = 1.0     # Minimize total delay across all buses


@dataclass
class Bus:
    """Represents a bus with its schedule."""
    id: str
    operator: str
    direction: str  # "Bengaluru->Kochi" or "Kochi->Bengaluru"
    departure_time: str  # HH:MM format
    
    def get_departure_minutes(self) -> int:
        """Convert departure time to minutes since midnight."""
        h, m = map(int, self.departure_time.split(':'))
        return h * 60 + m
    
    def is_forward_direction(self) -> bool:
        """Check if bus is going Bengaluru to Kochi."""
        return "Bengaluru" in self.direction and "Kochi" in self.direction.split("->")[1]


@dataclass
class Scenario:
    """Represents a complete scenario with buses and configuration."""
    id: str
    name: str
    description: str
    route: Route
    buses: List[Bus]
    weights: Weights = field(default_factory=Weights)
    
    def get_buses_by_operator(self, operator: str) -> List[Bus]:
        """Get all buses for a specific operator."""
        return [bus for bus in self.buses if bus.operator == operator]
    
    def get_all_operators(self) -> List[str]:
        """Get list of unique operators."""
        return list(set(bus.operator for bus in self.buses))


@dataclass
class ChargingStop:
    """Represents a single charging stop for a bus."""
    station_id: str
    arrival_time_min: int
    charge_start_time_min: int
    charge_end_time_min: int
    wait_time_min: int
    
    def format_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    @property
    def arrival_time(self) -> str:
        return self.format_time(self.arrival_time_min)
    
    @property
    def charge_start_time(self) -> str:
        return self.format_time(self.charge_start_time_min)
    
    @property
    def charge_end_time(self) -> str:
        return self.format_time(self.charge_end_time_min)


@dataclass
class BusSchedule:
    """Represents the complete schedule for a single bus."""
    bus_id: str
    operator: str
    direction: str
    departure_time: str
    arrival_time_min: int
    total_travel_time_min: int
    total_wait_time_min: int
    charging_stops: List[ChargingStop] = field(default_factory=list)
    
    def format_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    @property
    def arrival_time(self) -> str:
        return self.format_time(self.arrival_time_min)
    
    @property
    def total_time_min(self) -> int:
        """Total time including travel, charging, and waiting."""
        return self.total_travel_time_min + self.total_wait_time_min


@dataclass
class StationChargingEvent:
    """Represents a charging event at a station."""
    bus_id: str
    operator: str
    start_time_min: int
    end_time_min: int
    
    def format_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    @property
    def start_time(self) -> str:
        return self.format_time(self.start_time_min)
    
    @property
    def end_time(self) -> str:
        return self.format_time(self.end_time_min)


@dataclass
class Schedule:
    """Represents the complete schedule for all buses."""
    scenario_id: str
    bus_schedules: List[BusSchedule]
    station_schedules: Dict[str, List[StationChargingEvent]] = field(default_factory=dict)
    
    def get_bus_schedule(self, bus_id: str) -> Optional[BusSchedule]:
        """Get schedule for a specific bus."""
        for schedule in self.bus_schedules:
            if schedule.bus_id == bus_id:
                return schedule
        return None
    
    def get_total_delay(self) -> int:
        """Calculate total delay across all buses."""
        return sum(bs.total_wait_time_min for bs in self.bus_schedules)
    
    def get_max_individual_delay(self) -> int:
        """Get maximum delay for any single bus."""
        if not self.bus_schedules:
            return 0
        return max(bs.total_wait_time_min for bs in self.bus_schedules)
    
    def get_max_operator_delay(self) -> Dict[str, int]:
        """Get maximum total delay for each operator."""
        operator_delays = {}
        for bs in self.bus_schedules:
            if bs.operator not in operator_delays:
                operator_delays[bs.operator] = 0
            operator_delays[bs.operator] += bs.total_wait_time_min
        return operator_delays
