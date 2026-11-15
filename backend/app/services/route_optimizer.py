import math
from typing import List, Dict, Any, Tuple

NON_RAIL_DESTINATIONS = {
    "bali", "queenstown", "hawaii", "maui", "kauai", "oahu", "phuket",
    "santorini", "mykonos", "maldives", "varkala", "munnar", "manali",
    "shillong", "coorg", "ooty", "rishikesh", "kabini", "bora bora", "tahiti",
    "fiji", "seychelles", "mauritius", "zanzibar", "galapagos", "jeju",
    "langkawi", "koh samui", "krabi", "ibiza", "cappadocia", "siem reap",
    "iceland", "reykjavik", "akureyri", "tromso", "tromsø", "cusco", "cuzco",
    "malta", "cyprus", "andorra"
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

def is_water_crossing(lat1: float, lon1: float, lat2: float, lon2: float, destination: str = "") -> Tuple[bool, str]:
    """
    Detect whether travel between two coordinates crosses open water requiring a ferry or boat connection.
    Accounts for geographical boundaries (islands, straits, lagoon channels).
    """
    dest_l = (destination or "").lower()
    dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)

    # 1. Bali Mainland to Nusa Penida / Nusa Lembongan / Gili Islands
    if "bali" in dest_l or "indonesia" in dest_l or "denpasar" in dest_l:
        # Mainland Bali is west of lon 115.36; Nusa Penida / Lembongan are east of lon 115.42
        is_mainland_1 = lon1 < 115.36
        is_mainland_2 = lon2 < 115.36
        is_nusa_1 = lon1 >= 115.40 and -8.95 <= lat1 <= -8.60
        is_nusa_2 = lon2 >= 115.40 and -8.95 <= lat2 <= -8.60
        if (is_mainland_1 and is_nusa_2) or (is_nusa_1 and is_mainland_2):
            return True, "Ferry / Fast Boat Crossing (Badung Strait)"
        # Bali to Gili / Lombok
        if (lon1 < 115.5 and lon2 >= 115.9) or (lon2 < 115.5 and lon1 >= 115.9):
            return True, "Inter-Island Fast Boat (Lombok Strait)"

    # 2. Venice Lagoon to Outer Islands (Murano, Burano, Torcello, Lido)
    if "venice" in dest_l or "venezia" in dest_l:
        if dist_km > 1.5 and ((lat1 < 45.44 and lat2 > 45.45) or (lat1 > 45.45 and lat2 < 45.44)):
            return True, "Vaporetto / Water Bus Ferry"

    # 3. Thailand (Phuket to Phi Phi Islands / Railay / Koh Yao)
    if any(k in dest_l for k in ["phuket", "krabi", "phi phi", "koh samui", "koh phangan"]):
        if dist_km > 8.0:
            return True, "Speedboat / Ferry Transfer"

    # 4. Greece / Cyclades (Santorini, Mykonos, Crete, Rhodes)
    if any(k in dest_l for k in ["santorini", "mykonos", "crete", "rhodes", "corfu", "cyclades"]):
        if dist_km > 12.0:
            return True, "Inter-Island Ferry"

    return False, ""

def estimate_travel_transition(lat1: float, lon1: float, lat2: float, lon2: float, destination: str = "") -> Dict[str, Any]:
    """
    Estimate realistic travel mode, travel time, and distance between two geographic coordinates.
    Strictly validates destination rail availability: non-rail destinations (e.g. Bali, Queenstown, Hawaii)
    never receive Metro or Train suggestions. Accounts for open water ferry crossings.
    """
    dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    has_rail = destination_has_rail(destination)
    is_water, water_label = is_water_crossing(lat1, lon1, lat2, lon2, destination)

    if dist_km <= 0.05:
        return {
            "travel_mode": "Immediate / Within Complex",
            "mode": "Immediate / Within Complex",
            "travel_time": "1-2 min (Same complex)",
            "duration_minutes": 2,
            "distance": "Within complex",
            "distance_km": dist_km,
            "routing_methodology": "Co-located venue complex",
            "route_status": "Within complex",
            "status": "Within complex",
            "is_water_crossing": False,
            "water_body": None
        }

    if is_water:
        mode = "Ferry / Fast Boat Transfer"
        minutes = int(max(45, dist_km * 2.8))
        return {
            "travel_mode": mode,
            "mode": mode,
            "travel_time": f"{minutes} min (Subject to ferry schedule)",
            "duration_minutes": minutes,
            "distance": f"~{dist_km} km (Water Crossing)",
            "distance_km": dist_km,
            "routing_methodology": f"Ferry connection ({water_label})",
            "route_status": "Water / Ferry Crossing Needed",
            "status": "Water / Ferry Crossing Needed",
            "is_water_crossing": True,
            "water_body": water_label
        }

    dest_lower = (destination or "").lower()
    is_mrt_city = "singapore" in dest_lower
    transit_label = "Public Transit / MRT" if is_mrt_city else "Public Transit / Metro"

    if dist_km <= 1.5:
        mode = "Walking"
        minutes = int(dist_km * 12) + 4
    elif dist_km <= 12.0:
        mode = transit_label if has_rail else "Taxi / Rideshare"
        minutes = int(dist_km * 3.5) + 6
    elif dist_km <= 25.0:
        mode = transit_label if has_rail else "Taxi / Private Transfer"
        minutes = int(dist_km * 2.5) + 10
    else:
        mode = "Regional Train / Transit" if has_rail else "Private Driver / Road Transfer"
        minutes = int(dist_km * 2) + 15

    return {
        "travel_mode": mode,
        "mode": mode,
        "travel_time": f"{max(5, minutes)} min",
        "duration_minutes": max(5, minutes),
        "distance": f"{dist_km} km",
        "distance_km": dist_km,
        "routing_methodology": "Straight-line distance estimate (Haversine)",
        "route_status": "Straight-line estimate",
        "status": "Straight-line estimate",
        "is_water_crossing": False,
        "water_body": None
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

