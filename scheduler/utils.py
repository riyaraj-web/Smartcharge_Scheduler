"""
Utility functions for the scheduler.
"""

from typing import List, Tuple


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM time string to minutes since midnight."""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM format."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def calculate_travel_time(distance_km: float, speed_kmh: float) -> int:
    """Calculate travel time in minutes."""
    return int((distance_km / speed_kmh) * 60)


def get_stations_in_order(route, direction: str) -> List[str]:
    """Get list of station IDs in order for a given direction."""
    station_ids = [s.id for s in route.stations]
    
    if "Kochi->Bengaluru" in direction:
        # Reverse order for return direction
        return list(reversed(station_ids))
    
    return station_ids


def calculate_distance_between_points(route, from_point: str, to_point: str, direction: str) -> float:
    """Calculate distance between two points on the route."""
    segments = route.segments
    
    # For reverse direction, we need to reverse the segments
    if "Kochi->Bengaluru" in direction:
        segments = list(reversed(segments))
        # Also swap from/to in each segment
        segments = [type(seg)(from_point=seg.to_point, to_point=seg.from_point, distance_km=seg.distance_km) 
                   for seg in segments]
    
    distance = 0.0
    started = False
    
    for segment in segments:
        if segment.from_point == from_point:
            started = True
        
        if started:
            distance += segment.distance_km
            if segment.to_point == to_point:
                return distance
    
    return distance


def get_cumulative_distances(route, direction: str) -> dict:
    """
    Get cumulative distances from start to each station.
    Returns dict: {station_id: distance_from_start}
    """
    distances = {}
    current_distance = 0.0
    
    segments = route.segments
    if "Kochi->Bengaluru" in direction:
        segments = list(reversed(segments))
    
    for segment in segments:
        current_distance += segment.distance_km
        # Check if to_point is a station
        for station in route.stations:
            if station.id == segment.to_point:
                distances[station.id] = current_distance
                break
    
    return distances


def validate_battery_range(route, charging_stations: List[str], direction: str, battery_range_km: float) -> bool:
    """
    Validate that a bus can complete the trip with the given charging stations.
    Returns True if valid, False otherwise.
    """
    # Get all points in order (start, stations, end)
    if "Bengaluru->Kochi" in direction:
        start = "Bengaluru"
        end = "Kochi"
        all_points = [start] + charging_stations + [end]
    else:
        start = "Kochi"
        end = "Bengaluru"
        all_points = [start] + charging_stations + [end]
    
    # Check distance between consecutive charging points
    for i in range(len(all_points) - 1):
        from_point = all_points[i]
        to_point = all_points[i + 1]
        
        distance = calculate_distance_between_points(route, from_point, to_point, direction)
        
        if distance > battery_range_km:
            return False
    
    return True


def format_duration(minutes: int) -> str:
    """Format duration in minutes to human-readable string."""
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"
