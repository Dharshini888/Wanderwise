"""
osrm_provider.py — OSRM Road & Walking Routing Engine for WanderWise v8

Used ONLY for:
  1. Walking legs (User GPS -> Actual Boarding Stop, Transfer walking, Alighting Stop -> Destination)
  2. Road Alternatives (Driving routes via OSRM when public transit is unavailable)

RULE: OSRM must NEVER be represented as public transit (bus, train, etc.).
Road alternatives are returned in a separate 'road_alternative' payload.
"""

import logging
from typing import Dict, Any, Optional
from ...maps.osrm_service import get_osrm_route

logger = logging.getLogger(__name__)


class OSRMRoadProvider:
    """Provides OSRM walking and driving routes."""

    @staticmethod
    def get_walking_leg(
        from_name: str,
        from_lat: float,
        from_lon: float,
        to_name: str,
        to_lat: float,
        to_lon: float,
    ) -> Dict[str, Any]:
        """
        Calculates exact walking route geometry, distance, and duration
        from start coordinates to target coordinates using OSRM foot routing.
        """
        from ..station_normalizer import normalize_station_name
        fn_en = normalize_station_name(from_name)
        tn_en = normalize_station_name(to_name)

        route = get_osrm_route(from_lat, from_lon, to_lat, to_lon, mode="walking")
        if not route:
            from math import radians, cos, sin, asin, sqrt
            dlat = radians(to_lat - from_lat)
            dlon = radians(to_lon - from_lon)
            a = sin(dlat/2)**2 + cos(radians(from_lat)) * cos(radians(to_lat)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            dist_km = 6371 * c
            dist_m = int(dist_km * 1000)
            dur_mins = max(1, int(dist_m / 80)) # ~80m per min walk speed
            return {
                "type": "WALK",
                "mode": "Walk",
                "from_loc": {"name": fn_en, "lat": from_lat, "lon": from_lon},
                "to_loc": {"name": tn_en, "lat": to_lat, "lon": to_lon},
                "distance_m": dist_m,
                "duration_minutes": dur_mins,
                "provenance": "OSRM (Estimated Foot)",
            }

        return {
            "type": "WALK",
            "mode": "Walk",
            "from_loc": {"name": fn_en, "lat": from_lat, "lon": from_lon},
            "to_loc": {"name": tn_en, "lat": to_lat, "lon": to_lon},
            "distance_m": route.get("distance_m", int(route["distance_km"] * 1000)),
            "duration_minutes": route["duration_minutes"],
            "geometry": route.get("geometry", []),
            "provenance": "OSRM (Foot Routing)",
        }

    @staticmethod
    def get_road_alternative(
        origin_name: str,
        origin_lat: float,
        origin_lon: float,
        dest_name: str,
        dest_lat: float,
        dest_lon: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates driving road alternative using OSRM car routing.
        Returned ONLY under 'road_alternative' key when public transit is unavailable.
        Returns None if road route is geographically impossible or unavailable.
        """
        route = get_osrm_route(origin_lat, origin_lon, dest_lat, dest_lon)
        if not route or not route.get("distance_km") or route["distance_km"] <= 0:
            return None

        from ..station_normalizer import normalize_station_name
        orig_en = normalize_station_name(origin_name)
        dest_en = normalize_station_name(dest_name)

        dist_km = route["distance_km"]
        dur_mins = route["duration_minutes"]
        dur_str = f"{int(dur_mins // 60)}h {int(dur_mins % 60)}m" if dur_mins >= 60 else f"{int(dur_mins)}m"

        return {
            "type": "ROAD_ALTERNATIVE",
            "mode": "Driving",
            "provider": "OSRM",
            "origin": {"name": orig_en, "lat": origin_lat, "lon": origin_lon},
            "destination": {"name": dest_en, "lat": dest_lat, "lon": dest_lon},
            "distance_km": dist_km,
            "duration_minutes": dur_mins,
            "duration_min": dur_mins,
            "duration_display": dur_str,
            "verification_status": "Route Calculated",
            "geometry": route.get("geometry", []),
            "note": "Road driving route calculated via OSRM verified road network.",
        }
