import requests
import math
from typing import Dict, Any
from ..cache.transit_cache import TransitCache

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates straight-line distance in km between two lat/lon points."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

def get_osrm_route(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    """
    Fetches real driving route from OSRM (`router.project-osrm.org`).
    Returns: {"distance_km": float, "duration_minutes": float, "geometry": list, "source": str}
    """
    cache_key = f"osrm_{lat1:.4f}_{lon1:.4f}_{lat2:.4f}_{lon2:.4f}"
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        resp = requests.get(url, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("routes"):
                route = data["routes"][0]
                dist_km = round(route["distance"] / 1000.0, 1)
                dur_mins = round(route["duration"] / 60.0, 1)
                # OSRM returns [lon, lat], convert to [lat, lon] for Leaflet
                raw_coords = route.get("geometry", {}).get("coordinates", [])
                leaflet_geometry = [[c[1], c[0]] for c in raw_coords]

                result = {
                    "distance_km": dist_km,
                    "duration_minutes": dur_mins,
                    "geometry": leaflet_geometry,
                    "source": "Live (OSRM)"
                }
                TransitCache.set(cache_key, result)
                return result
    except Exception:
        pass

    # Fallback using Haversine + road multiplier
    direct_dist = haversine_distance(lat1, lon1, lat2, lon2)
    road_dist = round(max(direct_dist * 1.25, 5.0), 1)
    dur_mins = round((road_dist / 50.0) * 60.0, 1)  # Assume 50 km/h average speed

    fallback_result = {
        "distance_km": road_dist,
        "duration_minutes": dur_mins,
        "geometry": [[lat1, lon1], [lat2, lon2]],
        "source": "Haversine Estimate"
    }
    TransitCache.set(cache_key, fallback_result)
    return fallback_result
