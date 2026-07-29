import math
from typing import List, Dict, Any

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle distance between two points in kilometers."""
    R = 6371.0 # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_travel_transition(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    """Estimate travel mode, travel time, and distance between two geographic coordinates."""
    dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    if dist_km <= 1.2:
        mode = "Walking"
        minutes = int(dist_km * 12) + 4
    elif dist_km <= 5.0:
        mode = "Metro"
        minutes = int(dist_km * 4) + 6
    elif dist_km <= 15.0:
        mode = "Taxi"
        minutes = int(dist_km * 3) + 8
    else:
        mode = "Train"
        minutes = int(dist_km * 2) + 15

    return {
        "travel_mode": mode,
        "travel_time": f"{max(5, minutes)} min",
        "distance": f"{dist_km} km",
        "distance_km": dist_km
    }

def optimize_daily_route(pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort a list of POIs geographically using Nearest-Neighbor heuristic to minimize travel distance.
    """
    if not pois or len(pois) <= 1:
        return pois

    unvisited = list(pois)
    optimized = [unvisited.pop(0)] # Start with first POI (e.g. morning spot)

    while unvisited:
        curr = optimized[-1]
        curr_lat = curr.get("latitude") or curr.get("lat") or 0.0
        curr_lon = curr.get("longitude") or curr.get("lng") or 0.0

        # Find nearest neighbor
        best_idx = 0
        min_dist = float("inf")

        for idx, candidate in enumerate(unvisited):
            c_lat = candidate.get("latitude") or candidate.get("lat") or 0.0
            c_lon = candidate.get("longitude") or candidate.get("lng") or 0.0
            dist = haversine_distance_km(curr_lat, curr_lon, c_lat, c_lon)
            if dist < min_dist:
                min_dist = dist
                best_idx = idx

        next_poi = unvisited.pop(best_idx)
        optimized.append(next_poi)

    return optimized
