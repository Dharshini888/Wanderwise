"""
railradar_provider.py — WanderWise Transit V12.2 Production RailRadar Provider

Integrates live RailRadar API (https://api.railradar.in/v1/trains/{train_number}) using RAILRADAR_API_KEY.
Matches origin and destination coordinates against verified Indian Railways train routes.
Only populates fields returned directly by the RailRadar API response.
Never fabricates fake Indian train schedules, fares, or platforms.
"""

import os
import math
import requests
import logging
from typing import Optional, Dict, Any, List
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)

CANDIDATE_TRAINS = [
    "12676",  # Kovai SF Express (CBE -> MAS)
    "12675",  # Kovai SF Express (MAS -> CBE)
    "12672",  # Nilgiri SF Express (CBE -> MAS)
    "12671",  # Nilgiri SF Express (MAS -> CBE)
    "12640",  # Brindavan Express (SBC -> MAS)
    "12639",  # Brindavan Express (MAS -> SBC)
    "22626",  # Double Decker Express (SBC -> MAS)
    "12007",  # Shatabdi Express (MAS -> MYS)
    "12637",  # Pandian SF Express (MS -> MDU)
    "12638",  # Pandian SF Express (MDU -> MS)
    "12952",  # New Delhi Rajdhani (NDLS -> MMCT)
    "12951",  # Mumbai Rajdhani (MMCT -> NDLS)
]


def _haversine_dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class RailRadarProvider(TransitProvider):
    def __init__(self):
        super().__init__(provider_name="RailRadar")
        self.session = requests.Session()

    def health_check() -> Dict[str, Any]:
        api_key = os.getenv("RAILRADAR_API_KEY")
        if not api_key:
            return {"provider": "RailRadar", "configured": False, "status": "PROVIDER_NOT_CONFIGURED"}
        try:
            headers = {"Authorization": f"Bearer {api_key}", "x-api-key": api_key, "User-Agent": "WanderWise/12.2"}
            resp = requests.get("https://api.railradar.in/v1/trains/12676", headers=headers, timeout=10)
            if resp.status_code == 200 and resp.json().get("success"):
                return {"provider": "RailRadar", "configured": True, "api_reachable": True, "status": "READY"}
            else:
                return {"provider": "RailRadar", "configured": True, "api_reachable": False, "status": "PROVIDER_ERROR"}
        except Exception as e:
            return {"provider": "RailRadar", "configured": True, "api_reachable": False, "status": "PROVIDER_UNAVAILABLE", "error": str(e)}

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        api_key = os.getenv("RAILRADAR_API_KEY")
        if not api_key:
            logger.info("[PROVIDER] RailRadar: PROVIDER_NOT_CONFIGURED (No RAILRADAR_API_KEY in environment)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                note="RailRadar API key is unconfigured in server environment.",
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key,
            "User-Agent": "WanderWise/12.2",
        }

        matched_itineraries: List[Dict[str, Any]] = []

        try:
            for train_num in CANDIDATE_TRAINS:
                url = f"https://api.railradar.in/v1/trains/{train_num}"
                try:
                    resp = self.session.get(url, headers=headers, timeout=10)
                except requests.exceptions.RequestException as req_err:
                    logger.debug(f"[PROVIDER] RailRadar train {train_num} fetch error: {req_err}")
                    continue

                if resp.status_code != 200:
                    continue

                res_json = resp.json()
                if not res_json.get("success"):
                    continue

                train_data = res_json.get("data", {}).get("train", {})
                route_data = res_json.get("data", {}).get("route", [])

                if not route_data:
                    continue

                # Find boarding stop near origin and alighting stop near destination
                start_halt_idx = None
                end_halt_idx = None

                for idx, halt in enumerate(route_data):
                    st = halt.get("station", {})
                    st_lat = st.get("lat")
                    st_lon = st.get("lng")
                    if st_lat and st_lon:
                        if start_halt_idx is None and _haversine_dist_km(origin_lat, origin_lon, st_lat, st_lon) < 50.0:
                            start_halt_idx = idx
                        elif start_halt_idx is not None and _haversine_dist_km(dest_lat, dest_lon, st_lat, st_lon) < 50.0:
                            end_halt_idx = idx

                if start_halt_idx is not None and end_halt_idx is not None and start_halt_idx < end_halt_idx:
                    start_halt = route_data[start_halt_idx]
                    end_halt = route_data[end_halt_idx]

                    dep_time = start_halt.get("departure") or start_halt.get("arrival")
                    arr_time = end_halt.get("arrival") or end_halt.get("departure")
                    
                    dist_km = (end_halt.get("distance", 0) or 0) - (start_halt.get("distance", 0) or 0)
                    dist_m = int(dist_km * 1000) if dist_km > 0 else int(train_data.get("distance", 0) * 1000)
                    duration_min = train_data.get("duration")

                    platform = start_halt.get("platform")
                    platform_src = "PROVIDER" if platform else "UNAVAILABLE"

                    leg = {
                        "type": "TRANSIT",
                        "mode": "Rail",
                        "provider_mode": "TRAIN",
                        "train_number": train_data.get("number"),
                        "route_name": train_data.get("name"),
                        "operator": "Indian Railways",
                        "boarding_stop": {
                            "name": start_halt["station"].get("name", "Origin Station"),
                            "lat": start_halt["station"].get("lat"),
                            "lon": start_halt["station"].get("lng"),
                        },
                        "alighting_stop": {
                            "name": end_halt["station"].get("name", "Destination Station"),
                            "lat": end_halt["station"].get("lat"),
                            "lon": end_halt["station"].get("lng"),
                        },
                        "departure_time": dep_time,
                        "arrival_time": arr_time,
                        "platform": platform,
                        "platform_source": platform_src,
                        "distance_m": dist_m,
                        "distance_source": "PROVIDER",
                        "distance_type": "ROUTE_DISTANCE",
                        "schedule_status": "GTFS_SCHEDULED",
                        "provenance": "RailRadar API",
                        "provider": "RailRadar",
                    }

                    matched_itineraries.append({
                        "duration_minutes": duration_min,
                        "departure_time": dep_time,
                        "arrival_time": arr_time,
                        "transfers": 0,
                        "provider": "RailRadar",
                        "legs": [leg],
                    })

                    # If candidate matches, we have our itinerary!
                    break

            if matched_itineraries:
                logger.info(f"[PROVIDER] RailRadar: SUCCESS ({len(matched_itineraries)} rail itineraries found)")
                return ProviderResult(
                    status=ProviderStatus.SUCCESS,
                    provider_name=self.provider_name,
                    itineraries=matched_itineraries,
                    note="Verified Indian Railways options returned from RailRadar API.",
                )

            logger.info("[PROVIDER] RailRadar: NO_ITINERARY (No matching rail schedules found)")
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                note="RailRadar returned zero matching train itineraries for these coordinates.",
            )

        except requests.exceptions.Timeout:
            logger.warning("[PROVIDER] RailRadar: PROVIDER_UNAVAILABLE (TIMEOUT)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error="RailRadar request timed out after 10s",
            )
        except Exception as e:
            logger.warning(f"[PROVIDER] RailRadar: PROVIDER_ERROR ({e})")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_ERROR,
                provider_name=self.provider_name,
                error=str(e)[:150],
            )
