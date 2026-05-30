"""
Streamlit UI for Bus Charging Scheduler
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from scheduler import (
    load_all_scenarios, ChargingScheduler, Schedule
)
from scheduler.utils import format_duration


# Page configuration
st.set_page_config(
    page_title="Bus Charging Scheduler",
    page_icon="🚌",
    layout="wide"
)


@st.cache_data
def load_scenarios():
    """Load all scenarios (cached)."""
    return load_all_scenarios("scenarios")


@st.cache_data
def generate_schedule(scenario_id: str, scenario_name: str, scenario_desc: str, 
                      route_name: str, buses_data: list, weights_data: dict):
    """Generate schedule for a scenario (cached by inputs)."""
    # Reconstruct scenario from data
    from scheduler.models import Scenario, Bus, Weights
    from scheduler.scenario_loader import DEFAULT_ROUTE
    
    buses = [Bus(**bus) for bus in buses_data]
    weights = Weights(**weights_data)
    
    scenario = Scenario(
        id=scenario_id,
        name=scenario_name,
        description=scenario_desc,
        route=DEFAULT_ROUTE,
        buses=buses,
        weights=weights
    )
    
    scheduler = ChargingScheduler(time_limit_seconds=60)
    return scheduler.build_schedule(scenario)


def display_scenario_input(scenario):
    """Display scenario input data."""
    st.subheader("📋 Scenario Input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Route Configuration**")
        st.write(f"- Route: {scenario.route.name}")
        st.write(f"- Total Distance: {scenario.route.get_total_distance()} km")
        st.write(f"- Battery Range: {scenario.route.battery_range_km} km")
        st.write(f"- Speed: {scenario.route.speed_kmh} km/h")
        st.write(f"- Charging Time: {scenario.route.stations[0].charging_time_min} minutes")
        
        st.markdown("**Stations**")
        for station in scenario.route.stations:
            st.write(f"- {station.id}: {station.chargers} charger(s)")
    
    with col2:
        st.markdown("**Optimization Weights**")
        st.write(f"- Individual: {scenario.weights.individual}")
        st.write(f"- Operator: {scenario.weights.operator}")
        st.write(f"- Overall: {scenario.weights.overall}")
        
        st.markdown("**Fleet Summary**")
        st.write(f"- Total Buses: {len(scenario.buses)}")
        operators = scenario.get_all_operators()
        for operator in sorted(operators):
            count = len(scenario.get_buses_by_operator(operator))
            st.write(f"- {operator.upper()}: {count} buses")
    
    # Bus schedule table
    st.markdown("**Bus Departure Schedule**")
    bus_data = []
    for bus in scenario.buses:
        bus_data.append({
            "Bus ID": bus.id,
            "Operator": bus.operator.upper(),
            "Direction": bus.direction,
            "Departure": bus.departure_time
        })
    
    df = pd.DataFrame(bus_data)
    st.dataframe(df, width='stretch', hide_index=True)


def display_bus_schedules(schedule: Schedule):
    """Display per-bus timetables."""
    st.subheader("🚌 Per-Bus Timetables")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_delay = schedule.get_total_delay()
        st.metric("Total Delay", format_duration(total_delay))
    
    with col2:
        max_delay = schedule.get_max_individual_delay()
        st.metric("Max Individual Delay", format_duration(max_delay))
    
    with col3:
        operator_delays = schedule.get_max_operator_delay()
        max_op_delay = max(operator_delays.values()) if operator_delays else 0
        st.metric("Max Operator Delay", format_duration(max_op_delay))
    
    with col4:
        avg_delay = total_delay / len(schedule.bus_schedules) if schedule.bus_schedules else 0
        st.metric("Avg Delay per Bus", format_duration(int(avg_delay)))
    
    # Detailed bus schedules
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 Table View", "📝 Detailed View"])
    
    with tab1:
        # Compact table view
        table_data = []
        for bus_schedule in schedule.bus_schedules:
            stations_used = ", ".join([stop.station_id for stop in bus_schedule.charging_stops])
            table_data.append({
                "Bus ID": bus_schedule.bus_id,
                "Operator": bus_schedule.operator.upper(),
                "Direction": bus_schedule.direction,
                "Departure": bus_schedule.departure_time,
                "Arrival": bus_schedule.arrival_time,
                "Stations Used": stations_used,
                "# Charges": len(bus_schedule.charging_stops),
                "Wait Time": format_duration(bus_schedule.total_wait_time_min),
                "Total Time": format_duration(bus_schedule.total_time_min)
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, width='stretch', hide_index=True)
    
    with tab2:
        # Detailed view with expandable sections
        for bus_schedule in schedule.bus_schedules:
            with st.expander(f"🚌 {bus_schedule.bus_id} ({bus_schedule.operator.upper()})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Direction:** {bus_schedule.direction}")
                    st.write(f"**Departure:** {bus_schedule.departure_time}")
                    st.write(f"**Arrival:** {bus_schedule.arrival_time}")
                
                with col2:
                    st.write(f"**Travel Time:** {format_duration(bus_schedule.total_travel_time_min)}")
                    st.write(f"**Wait Time:** {format_duration(bus_schedule.total_wait_time_min)}")
                    st.write(f"**Total Time:** {format_duration(bus_schedule.total_time_min)}")
                
                with col3:
                    st.write(f"**Charging Stops:** {len(bus_schedule.charging_stops)}")
                
                if bus_schedule.charging_stops:
                    st.markdown("**Charging Timeline:**")
                    
                    charging_data = []
                    for stop in bus_schedule.charging_stops:
                        charging_data.append({
                            "Station": stop.station_id,
                            "Arrival": stop.arrival_time,
                            "Charge Start": stop.charge_start_time,
                            "Charge End": stop.charge_end_time,
                            "Wait Time": format_duration(stop.wait_time_min)
                        })
                    
                    df_charging = pd.DataFrame(charging_data)
                    st.dataframe(df_charging, width='stretch', hide_index=True)


def display_station_schedules(schedule: Schedule, scenario):
    """Display per-station charging schedules."""
    st.subheader("⚡ Per-Station Charging Schedules")
    
    for station in scenario.route.stations:
        with st.expander(f"Station {station.id}", expanded=True):
            events = schedule.station_schedules.get(station.id, [])
            
            if not events:
                st.info(f"No buses charged at station {station.id}")
                continue
            
            st.write(f"**Total Charges:** {len(events)}")
            
            # Create timeline data
            timeline_data = []
            for i, event in enumerate(events):
                timeline_data.append({
                    "Order": i + 1,
                    "Bus ID": event.bus_id,
                    "Operator": event.operator.upper(),
                    "Start Time": event.start_time,
                    "End Time": event.end_time,
                    "Duration": "25 min"
                })
            
            df = pd.DataFrame(timeline_data)
            st.dataframe(df, width='stretch', hide_index=True)
            
            # Check for overlaps (should be none)
            overlaps = []
            for i in range(len(events) - 1):
                if events[i].end_time_min > events[i + 1].start_time_min:
                    overlaps.append((events[i].bus_id, events[i + 1].bus_id))
            
            if overlaps:
                st.error(f"⚠️ Overlaps detected: {overlaps}")
            else:
                st.success("✅ No overlaps - all charges properly sequenced")


def main():
    st.title("🚌 Bus Charging Scheduler")
    st.markdown("**Intelligent scheduling for electric bus charging stations**")
    st.markdown("---")
    
    # Load scenarios
    scenarios = load_scenarios()
    
    if not scenarios:
        st.error("No scenarios found. Please ensure scenario files are in the 'scenarios' directory.")
        return
    
    # Scenario selector
    scenario_names = [f"{s.id}: {s.name}" for s in scenarios]
    selected_idx = st.selectbox(
        "Select a scenario:",
        range(len(scenarios)),
        format_func=lambda i: scenario_names[i]
    )
    
    scenario = scenarios[selected_idx]
    
    # Display scenario description
    st.info(f"**{scenario.name}**: {scenario.description}")
    
    # Display scenario input
    with st.container():
        display_scenario_input(scenario)
    
    st.markdown("---")
    
    # Generate schedule button
    if st.button("🚀 Generate Schedule", type="primary", width='stretch'):
        with st.spinner("Optimizing charging schedule... This may take up to 60 seconds."):
            # Prepare data for caching
            buses_data = [
                {
                    'id': bus.id,
                    'operator': bus.operator,
                    'direction': bus.direction,
                    'departure_time': bus.departure_time
                }
                for bus in scenario.buses
            ]
            
            weights_data = {
                'individual': scenario.weights.individual,
                'operator': scenario.weights.operator,
                'overall': scenario.weights.overall
            }
            
            schedule = generate_schedule(
                scenario.id,
                scenario.name,
                scenario.description,
                scenario.route.name,
                buses_data,
                weights_data
            )
            
            st.success("✅ Schedule generated successfully!")
            
            # Store in session state
            st.session_state['schedule'] = schedule
            st.session_state['scenario'] = scenario
    
    # Display results if available
    if 'schedule' in st.session_state and 'scenario' in st.session_state:
        schedule = st.session_state['schedule']
        scenario = st.session_state['scenario']
        
        st.markdown("---")
        
        # Display results
        display_bus_schedules(schedule)
        
        st.markdown("---")
        
        display_station_schedules(schedule, scenario)


if __name__ == "__main__":
    main()
