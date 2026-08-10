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
from app.services.maps.osrm_service import get_osrm_route

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
        route = get_osrm_route(from_lat, from_lon, to_lat, to_lon)
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
                "mode": "WALK",
                "from_loc": {"name": from_name, "lat": from_lat, "lon": from_lon},
                "to_loc": {"name": to_name, "lat": to_lat, "lon": to_lon},
                "distance_m": dist_m,
                "duration_minutes": dur_mins,
                "provenance": "OSRM (Estimated Foot)",
            }

        return {
            "type": "WALK",
            "mode": "WALK",
            "from_loc": {"name": from_name, "lat": from_lat, "lon": from_lon},
            "to_loc": {"name": to_name, "lat": to_lat, "lon": to_lon},
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
    ) -> Dict[str, Any]:
        """
        Calculates driving road alternative using OSRM car routing.
        Returned ONLY under 'road_alternative' key when public transit is unavailable.
        """
        route = get_osrm_route(origin_lat, origin_lon, dest_lat, dest_lon)
        dist_km = route["distance_km"] if route else 0.0
        dur_mins = route["duration_minutes"] if route else 0
        dur_str = f"{int(dur_mins // 60)}h {int(dur_mins % 60)}m" if dur_mins >= 60 else f"{int(dur_mins)}m"

        return {
            "type": "ROAD_ALTERNATIVE",
            "mode": "DRIVING",
            "provider": "OSRM",
            "origin": {"name": origin_name, "lat": origin_lat, "lon": origin_lon},
            "destination": {"name": dest_name, "lat": dest_lat, "lon": dest_lon},
            "distance_km": dist_km,
            "duration_minutes": dur_mins,
            "duration_display": dur_str,
            "geometry": route.get("geometry", []) if route else [],
            "note": "Road driving route calculated via OSRM. Public transit schedule unavailable.",
        }
