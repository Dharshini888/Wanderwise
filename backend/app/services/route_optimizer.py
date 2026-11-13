import math
from typing import List, Dict, Any, Tuple

NON_RAIL_DESTINATIONS = {
    "bali", "queenstown", "hawaii", "maui", "kauai", "oahu", "phuket",
    "santorini", "mykonos", "maldives", "varkala", "munnar", "manali",
    "shillong", "coorg", "ooty", "rishikesh", "kabini", "bora bora", "tahiti",
    "fiji", "seychelles", "mauritius", "zanzibar", "galapagos", "jeju",
    "langkawi", "koh samui", "krabi", "ibiza", "cappadocia", "siem reap"
}

def destination_has_rail(destination: str) -> bool:
    """Check if destination has active passenger rail, metro, or subway infrastructure."""
    if not destination:
        return True
    dest_l = destination.strip().lower()
    for nr in NON_RAIL_DESTINATIONS:
        if nr in dest_l:
            return False
    return True

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle distance between two points in kilometers."""
    R = 6371.0 # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_travel_transition(lat1: float, lon1: float, lat2: float, lon2: float, destination: str = "") -> Dict[str, Any]:
    """
    Estimate realistic travel mode, travel time, and distance between two geographic coordinates.
    Strictly validates destination rail availability: non-rail destinations (e.g. Bali, Queenstown, Hawaii)
    never receive Metro or Train suggestions.
    """
    dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    has_rail = destination_has_rail(destination)

    if dist_km <= 1.5:
        mode = "Walking"
        minutes = int(dist_km * 12) + 4
    elif dist_km <= 5.0:
        mode = "Taxi / Rideshare" if not has_rail else "Public Transit / Metro"
        minutes = int(dist_km * 4) + 6
    elif dist_km <= 15.0:
        mode = "Taxi / Private Transfer" if not has_rail else "Taxi"
        minutes = int(dist_km * 3) + 8
    else:
        mode = "Private Driver / Road Transfer" if not has_rail else "Regional Train / Transit"
        minutes = int(dist_km * 2) + 15

    return {
        "travel_mode": mode,
        "travel_time": f"{max(5, minutes)} min",
        "distance": f"{dist_km} km",
        "distance_km": dist_km,
        "routing_methodology": "Straight-line distance estimate (Haversine)",
        "route_status": "Straight-line estimate"
    }

def optimize_daily_route(pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort a list of POIs or activities geographically using Nearest-Neighbor heuristic to minimize travel distance.
    Supports both direct POI dicts and scheduled activity objects with nested 'place' dicts.
    """
    if not pois or len(pois) <= 1:
        return pois

    def _extract_coords(item: Dict[str, Any]) -> Tuple[float, float]:
        p = item.get("place") if isinstance(item.get("place"), dict) else {}
        lat = item.get("latitude") or item.get("lat") or p.get("latitude") or p.get("lat")
        lon = item.get("longitude") or item.get("lon") or item.get("lng") or p.get("longitude") or p.get("lng")
        try:
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        except (ValueError, TypeError):
            pass
        return 0.0, 0.0

    unvisited = list(pois)
    optimized = [unvisited.pop(0)]  # Start with first stop (e.g. morning anchor or hotel start)

    while unvisited:
        curr = optimized[-1]
        curr_lat, curr_lon = _extract_coords(curr)

        if curr_lat == 0.0 and curr_lon == 0.0:
            optimized.append(unvisited.pop(0))
            continue

        best_idx = 0
        min_dist = float("inf")

        for idx, candidate in enumerate(unvisited):
            c_lat, c_lon = _extract_coords(candidate)
            if c_lat == 0.0 and c_lon == 0.0:
                dist = 999.0
            else:
                dist = haversine_distance_km(curr_lat, curr_lon, c_lat, c_lon)
            if dist < min_dist:
                min_dist = dist
                best_idx = idx

        next_poi = unvisited.pop(best_idx)
        optimized.append(next_poi)

    return optimized

