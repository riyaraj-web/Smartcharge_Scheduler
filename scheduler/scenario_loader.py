"""
Scenario and route configuration loader.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from .models import (
    Scenario, Bus, Route, RouteSegment, Station, Weights
)


# Default route configuration
DEFAULT_ROUTE = Route(
    name="Bengaluru-Kochi",
    segments=[
        RouteSegment("Bengaluru", "A", 100),
        RouteSegment("A", "B", 120),
        RouteSegment("B", "C", 100),
        RouteSegment("C", "D", 120),
        RouteSegment("D", "Kochi", 100),
    ],
    stations=[
        Station("A", chargers=1, charging_time_min=25),
        Station("B", chargers=1, charging_time_min=25),
        Station("C", chargers=1, charging_time_min=25),
        Station("D", chargers=1, charging_time_min=25),
    ],
    battery_range_km=240.0,
    speed_kmh=60.0
)


def load_route(route_path: Optional[str] = None) -> Route:
    """
    Load route configuration from JSON file.
    If no path provided, returns default route.
    """
    if route_path is None:
        return DEFAULT_ROUTE
    
    with open(route_path, 'r') as f:
        data = json.load(f)
    
    segments = [
        RouteSegment(
            from_point=seg['from'],
            to_point=seg['to'],
            distance_km=seg['distance_km']
        )
        for seg in data['segments']
    ]
    
    stations = [
        Station(
            id=st['id'],
            chargers=st.get('chargers', 1),
            charging_time_min=st.get('charging_time_min', 25)
        )
        for st in data['stations']
    ]
    
    return Route(
        name=data['name'],
        segments=segments,
        stations=stations,
        battery_range_km=data.get('battery_range_km', 240.0),
        speed_kmh=data.get('speed_kmh', 60.0)
    )


def load_scenario(scenario_path: str, route: Optional[Route] = None) -> Scenario:
    """
    Load a scenario from JSON file.
    
    Args:
        scenario_path: Path to scenario JSON file
        route: Optional route configuration (uses default if not provided)
    
    Returns:
        Loaded scenario
    """
    if route is None:
        route = DEFAULT_ROUTE
    
    with open(scenario_path, 'r') as f:
        data = json.load(f)
    
    buses = [
        Bus(
            id=bus['id'],
            operator=bus['operator'],
            direction=bus['direction'],
            departure_time=bus['departure_time']
        )
        for bus in data['buses']
    ]
    
    weights_data = data.get('weights', {})
    weights = Weights(
        individual=weights_data.get('individual', 1.0),
        operator=weights_data.get('operator', 1.0),
        overall=weights_data.get('overall', 1.0)
    )
    
    return Scenario(
        id=data['id'],
        name=data['name'],
        description=data['description'],
        route=route,
        buses=buses,
        weights=weights
    )


def load_all_scenarios(scenarios_dir: str = "scenarios", route: Optional[Route] = None) -> List[Scenario]:
    """
    Load all scenarios from a directory.
    
    Args:
        scenarios_dir: Directory containing scenario JSON files
        route: Optional route configuration
    
    Returns:
        List of loaded scenarios
    """
    scenarios_path = Path(scenarios_dir)
    if not scenarios_path.exists():
        return []
    
    scenarios = []
    for scenario_file in sorted(scenarios_path.glob("scenario_*.json")):
        try:
            scenario = load_scenario(str(scenario_file), route)
            scenarios.append(scenario)
        except Exception as e:
            print(f"Error loading {scenario_file}: {e}")
    
    return scenarios


def save_scenario(scenario: Scenario, output_path: str):
    """
    Save a scenario to JSON file.
    
    Args:
        scenario: Scenario to save
        output_path: Path to output JSON file
    """
    data = {
        'id': scenario.id,
        'name': scenario.name,
        'description': scenario.description,
        'route': scenario.route.name,
        'weights': {
            'individual': scenario.weights.individual,
            'operator': scenario.weights.operator,
            'overall': scenario.weights.overall
        },
        'buses': [
            {
                'id': bus.id,
                'operator': bus.operator,
                'direction': bus.direction,
                'departure_time': bus.departure_time
            }
            for bus in scenario.buses
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
