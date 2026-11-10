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

def get_osrm_route(lat1: float, lon1: float, lat2: float, lon2: float, mode: str = "driving") -> Dict[str, Any]:
    """
    Fetches real driving or walking route from OSRM (`router.project-osrm.org`)
    or falls back to calibrated mode-aware routing estimate.
    Returns: {"distance_km": float, "duration_minutes": float, "geometry": list, "source": str}
    """
    mode_clean = str(mode or "driving").lower()
    osrm_profile = "walking" if "walk" in mode_clean else "driving"
    cache_key = f"osrm_{osrm_profile}_{lat1:.4f}_{lon1:.4f}_{lat2:.4f}_{lon2:.4f}"
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    direct_dist = haversine_distance(lat1, lon1, lat2, lon2)

    try:
        url = f"https://router.project-osrm.org/route/v1/{osrm_profile}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        resp = requests.get(url, timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("routes"):
                route = data["routes"][0]
                dist_km = round(route["distance"] / 1000.0, 2)
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

    # Calibrated fallback respecting realistic urban geometry and transport mode
    road_dist = round(direct_dist * 1.2, 2) if direct_dist > 0.05 else round(direct_dist, 2)
    
    if "walk" in mode_clean:
        # Walking speed ~ 4.5 km/h
        dur_mins = round(max(2.0, (road_dist / 4.5) * 60.0), 1)
    elif "transit" in mode_clean or "metro" in mode_clean or "bus" in mode_clean:
        # Transit speed ~ 25 km/h plus 5-min transit buffer
        dur_mins = round(5.0 + (road_dist / 25.0) * 60.0, 1)
    else:
        # Driving speed ~ 35 km/h in city
        dur_mins = round(max(3.0, (road_dist / 35.0) * 60.0), 1)

    fallback_result = {
        "distance_km": road_dist,
        "duration_minutes": dur_mins,
        "geometry": [[lat1, lon1], [lat2, lon2]],
        "source": "Calibrated Routing Estimate"
    }
    TransitCache.set(cache_key, fallback_result)
    return fallback_result
