"""
location_normalizer.py — Location Normalization & Sanity Check Service for WanderWise V12

Responsibilities:
  1. Validate coordinate bounds (-90 <= lat <= 90, -180 <= lon <= 180).
  2. Extract ISO country_code, country, city, continent, display_name.
  3. Calculate Haversine straight-line distance.
  4. Perform SAME_LOCATION check (distance < 0.5 km).
  5. Check OSRM distance / straight-line ratio for ROUTE_SANITY_WARNING.
"""

import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates straight-line distance in km between two lat/lon pairs."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def normalize_location(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes location dictionary and validates coordinate boundaries.
    """
    lat = input_data.get("lat") or input_data.get("latitude")
    lon = input_data.get("lon") or input_data.get("longitude")

    if lat is None or lon is None:
        raise ValueError("Missing latitude or longitude in location input")

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid non-numeric coordinates: lat={lat}, lon={lon}")

    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of bounds [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of bounds [-180, 180]: {lon}")

    return {
        "name": input_data.get("name") or input_data.get("display_name") or "Location",
        "display_name": input_data.get("display_name") or input_data.get("name") or "Location",
        "latitude": lat,
        "longitude": lon,
        "lat": lat,
        "lon": lon,
        "country_code": (input_data.get("country_code") or "").upper(),
        "country": input_data.get("country") or "",
        "city": input_data.get("city") or "",
        "source": input_data.get("source") or "Geolocation",
        "accuracy_m": input_data.get("accuracy_m") or input_data.get("accuracy"),
    }


def check_location_sanity(origin: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates origin and destination coordinates for SAME_LOCATION (< 0.5 km)
    and straight-line distance calculations.
    """
    try:
        norm_orig = normalize_location(origin)
        norm_dest = normalize_location(destination)
    except ValueError as e:
        logger.warning(f"[LOCATION SANITY] Normalization failed: {e}")
        return {
            "same_location": False,
            "straight_line_distance_km": 0.0,
            "warning": str(e),
        }

    dist_km = round(_haversine_km(
        norm_orig["latitude"], norm_orig["longitude"],
        norm_dest["latitude"], norm_dest["longitude"]
    ), 3)

    is_same = dist_km < 0.5

    if is_same:
        logger.info(f"[LOCATION SANITY] SAME_LOCATION detected! Distance: {dist_km} km ({norm_orig['name']} -> {norm_dest['name']})")

    return {
        "same_location": is_same,
        "straight_line_distance_km": dist_km,
        "origin_normalized": norm_orig,
        "destination_normalized": norm_dest,
        "warning": None,
    }


def validate_route_sanity(straight_line_km: float, road_distance_km: float) -> Optional[str]:
    """
    Flags ROUTE_SANITY_WARNING if road distance ratio is abnormally large compared to straight-line distance.
    """
    if straight_line_km <= 0 or road_distance_km <= 0:
        return None
    ratio = road_distance_km / straight_line_km
    if ratio > 5.0 and straight_line_km < 10.0:
        logger.warning(f"[ROUTE SANITY] Abnormal detour detected: straight={straight_line_km}km, road={road_distance_km}km (ratio: {ratio:.1f})")
        return "ROUTE_SANITY_WARNING: Road routing produces abnormal detour ratio compared to straight-line distance."
    return None
