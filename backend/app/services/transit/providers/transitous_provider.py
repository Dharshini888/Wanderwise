"""
transitous_provider.py — Primary Transit Provider for WanderWise v10

Queries live MOTIS routing engine on https://api.transitous.org/api/v1/plan
using coordinate-based `fromPlace` and `toPlace` parameters.

V10 Enhancements:
  - Robust timestamp parsing (ISO 8601, ISO offset, unix ms, unix sec).
  - Strict Chronology Validation (rejects impossible itineraries where arr > next dep).
  - Strict Platform Provenance (platform_source = "PROVIDER" or "UNAVAILABLE").
  - Isolated Distance Provenance (distance_source = "PROVIDER" or "HAVERSINE").
  - Mode Normalization (provider_mode vs mode).
"""

import math
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)

TRANSITOUS_API_URL = "https://api.transitous.org/api/v1/plan"


def _parse_time_to_dt(ts: Any) -> Optional[datetime]:
    """Parse ISO 8601, offset strings, or numeric timestamps to datetime."""
    if not ts:
        return None
    try:
        if isinstance(ts, str):
            clean_ts = ts.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_ts)
        elif isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts / 1000.0 if ts > 1e11 else ts)
    except Exception:
        pass
    return None


def _format_dt(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%H:%M") if dt else None


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculates straight-line distance in meters between two lat/lon points."""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(R * c)


def _normalize_mode(raw_mode: str) -> tuple[str, str]:
    """Returns (provider_mode, normalized_mode)."""
    pm = (raw_mode or "WALK").upper()
    mapping = {
        "WALK": "Walk",
        "SUBWAY": "Subway",
        "BUS": "Bus",
        "RAIL": "Rail",
        "TRAIN": "Train",
        "LONG_DISTANCE": "Long Distance Rail",
        "HIGHSPEED_RAIL": "Highspeed Rail",
        "REGIONAL_RAIL": "Regional Rail",
        "NIGHT_RAIL": "Night Rail",
        "SUBURBAN": "Suburban Rail",
        "TRAM": "Tram",
        "FERRY": "Ferry",
        "TRANSFER": "Transfer",
    }
    nm = mapping.get(pm, pm.replace("_", " ").title())
    return pm, nm


def _validate_chronology(parsed_legs: List[Dict[str, Any]], start_dt: Optional[datetime], end_dt: Optional[datetime]) -> bool:
    """Rejects itineraries with impossible leg order (arrival > next departure)."""
    if start_dt and end_dt and start_dt > end_dt:
        return False
    prev_arr_dt = None
    for leg in parsed_legs:
        leg_dep_dt = leg.get("_dep_dt")
        leg_arr_dt = leg.get("_arr_dt")
        if prev_arr_dt and leg_dep_dt and prev_arr_dt > leg_dep_dt:
            return False
        if leg_dep_dt and leg_arr_dt and leg_dep_dt > leg_arr_dt:
            return False
        if leg_arr_dt:
            prev_arr_dt = leg_arr_dt
    return True


class TransitousProvider(TransitProvider):
    def __init__(self):
        super().__init__(provider_name="Transitous")

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        params = {
            "fromPlace": f"{origin_lat},{origin_lon}",
            "toPlace": f"{dest_lat},{dest_lon}",
            "numItineraries": 3,
            "mode": "TRANSIT,WALK",
        }
        headers = {"User-Agent": "WanderWise/10.0 (contact@wanderwise.ai)"}

        logger.info(f"[Transitous] Request: {TRANSITOUS_API_URL}?fromPlace={params['fromPlace']}&toPlace={params['toPlace']}")

        try:
            resp = requests.get(TRANSITOUS_API_URL, params=params, headers=headers, timeout=10)
            logger.info(f"[Transitous] HTTP status: {resp.status_code}")
        except requests.exceptions.Timeout:
            logger.warning("[Transitous] Coverage/status: PROVIDER_UNAVAILABLE (TIMEOUT)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error="Request to Transitous timed out after 10 seconds",
                note="Transit provider timed out.",
            )
        except requests.exceptions.ConnectionError as e:
            err_str = str(e)
            logger.warning(f"[Transitous] Coverage/status: PROVIDER_UNAVAILABLE (Connection error: {err_str[:120]})")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=f"Connection error: {err_str[:120]}",
                note="Transit provider could not be reached (DNS or network connection error).",
            )
        except Exception as e:
            logger.warning(f"[Transitous] Coverage/status: PROVIDER_UNAVAILABLE ({e})")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=str(e)[:200],
            )

        if resp.status_code != 200:
            logger.warning(f"[Transitous] Coverage/status: PROVIDER_UNAVAILABLE (HTTP {resp.status_code})")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=f"HTTP status {resp.status_code}",
            )

        try:
            data = resp.json()
        except Exception as e:
            logger.warning(f"[Transitous] Coverage/status: PROVIDER_UNAVAILABLE (Malformed JSON)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=f"Malformed JSON response: {e}",
            )

        itineraries = data.get("itineraries", [])
        if not itineraries and isinstance(data.get("plan"), dict):
            itineraries = data["plan"].get("itineraries", [])

        logger.info(f"[Transitous] Response itinerary count: {len(itineraries)}")

        if not itineraries:
            logger.info("[Transitous] Coverage/status: NO_ITINERARY")
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                note="No public transit itineraries found for this route and region.",
            )

        parsed_itineraries = []
        for it in itineraries:
            raw_legs = it.get("legs", [])
            parsed_legs = []

            for leg in raw_legs:
                provider_mode, mode = _normalize_mode(leg.get("mode"))
                from_obj = leg.get("from", {})
                to_obj = leg.get("to", {})

                start_ts = (
                    leg.get("startTime")
                    or leg.get("departureTime")
                    or from_obj.get("departure")
                    or from_obj.get("scheduledDeparture")
                )
                end_ts = (
                    leg.get("endTime")
                    or leg.get("arrivalTime")
                    or to_obj.get("arrival")
                    or to_obj.get("scheduledArrival")
                )

                dep_dt = _parse_time_to_dt(start_ts)
                arr_dt = _parse_time_to_dt(end_ts)

                start_time_str = _format_dt(dep_dt)
                end_time_str = _format_dt(arr_dt)

                duration_mins = (
                    int(leg.get("duration") / 60)
                    if leg.get("duration") is not None
                    else None
                )

                # Distance parsing
                dist_m = leg.get("distance")
                dist_source = "PROVIDER"
                dist_type = "ROUTE_DISTANCE"
                if dist_m is None or dist_m == 0:
                    f_lat, f_lon = from_obj.get("lat"), from_obj.get("lon")
                    t_lat, t_lon = to_obj.get("lat"), to_obj.get("lon")
                    if f_lat and f_lon and t_lat and t_lon:
                        dist_m = _haversine_meters(f_lat, f_lon, t_lat, t_lon)
                        dist_source = "HAVERSINE"
                        dist_type = "STRAIGHT_LINE_ESTIMATE"
                    else:
                        dist_m = 0
                else:
                    dist_m = int(dist_m)

                if provider_mode == "WALK":
                    parsed_legs.append({
                        "type": "WALK",
                        "mode": "Walk",
                        "provider_mode": "WALK",
                        "from_loc": {
                            "name": from_obj.get("name") or "Origin Point",
                            "lat": from_obj.get("lat"),
                            "lon": from_obj.get("lon"),
                        },
                        "to_loc": {
                            "name": to_obj.get("name") or "Boarding Point",
                            "lat": to_obj.get("lat"),
                            "lon": to_obj.get("lon"),
                        },
                        "departure_time": start_time_str,
                        "arrival_time": end_time_str,
                        "_dep_dt": dep_dt,
                        "_arr_dt": arr_dt,
                        "distance_m": dist_m,
                        "duration_minutes": duration_mins,
                        "distance_source": dist_source,
                        "distance_type": dist_type,
                        "provenance": "GTFS / MOTIS",
                    })
                elif provider_mode == "TRANSFER":
                    parsed_legs.append({
                        "type": "TRANSFER",
                        "mode": "Transfer",
                        "provider_mode": "TRANSFER",
                        "from_loc": {
                            "name": from_obj.get("name") or "Arrival Platform",
                            "lat": from_obj.get("lat"),
                            "lon": from_obj.get("lon"),
                        },
                        "to_loc": {
                            "name": to_obj.get("name") or "Departure Platform",
                            "lat": to_obj.get("lat"),
                            "lon": to_obj.get("lon"),
                        },
                        "departure_time": start_time_str,
                        "arrival_time": end_time_str,
                        "_dep_dt": dep_dt,
                        "_arr_dt": arr_dt,
                        "duration_minutes": duration_mins or 3,
                        "provenance": "GTFS / MOTIS",
                    })
                else: # TRANSIT (BUS, RAIL, SUBWAY, HIGHSPEED_RAIL, etc.)
                    route_name = (
                        leg.get("routeShortName")
                        or leg.get("routeLongName")
                        or leg.get("route")
                    )
                    headsign = leg.get("tripHeadsign") or leg.get("headsign")
                    agency = leg.get("agencyName") or leg.get("agencyId")

                    raw_platform = (
                        from_obj.get("scheduledTrack")
                        or from_obj.get("track")
                        or from_obj.get("platformCode")
                        or leg.get("departureTrack")
                    )
                    if raw_platform == "-":
                        raw_platform = None

                    platform = raw_platform if raw_platform else None
                    platform_source = "PROVIDER" if raw_platform else "UNAVAILABLE"

                    intermediate_stops = leg.get("intermediateStops")
                    stops_cnt = len(intermediate_stops) if isinstance(intermediate_stops, list) else (leg.get("numStops") or leg.get("intermediateStopsCount"))

                    # GTFS Scheduled badge ONLY when both dep_dt & arr_dt exist
                    time_status = "SCHEDULED" if (dep_dt and arr_dt) else ("VERIFIED" if dep_dt else "UNAVAILABLE")

                    parsed_legs.append({
                        "type": "TRANSIT",
                        "mode": mode,
                        "provider_mode": provider_mode,
                        "route_name": route_name if route_name else None,
                        "route_number": route_name if route_name else None,
                        "headsign": headsign if headsign else None,
                        "agency": agency if agency else None,
                        "boarding_stop": {
                            "name": from_obj.get("name") or "Transit Station",
                            "lat": from_obj.get("lat"),
                            "lon": from_obj.get("lon"),
                        },
                        "alighting_stop": {
                            "name": to_obj.get("name") or "Destination Station",
                            "lat": to_obj.get("lat"),
                            "lon": to_obj.get("lon"),
                        },
                        "departure_time": start_time_str,
                        "arrival_time": end_time_str,
                        "_dep_dt": dep_dt,
                        "_arr_dt": arr_dt,
                        "time_status": time_status,
                        "platform": platform,
                        "platform_source": platform_source,
                        "platform_status": platform_source,
                        "stops_count": stops_cnt,
                        "duration_minutes": duration_mins,
                        "distance_m": dist_m,
                        "distance_source": dist_source,
                        "distance_type": dist_type,
                        "fare": {
                            "amount": None,
                            "currency": None,
                            "source": "GTFS",
                            "status": "UNAVAILABLE"
                        },
                        "provenance": "GTFS",
                        "schedule_type": "SCHEDULED" if (dep_dt and arr_dt) else "UNTIMED"
                    })

            start_dt = _parse_time_to_dt(it.get("startTime") or it.get("departureTime"))
            end_dt = _parse_time_to_dt(it.get("endTime") or it.get("arrivalTime"))

            # Step 5: Chronology Validation
            if not _validate_chronology(parsed_legs, start_dt, end_dt):
                logger.warning("[Transitous] Chronology validation failed for itinerary (skipping invalid itinerary)")
                continue

            # Strip temporary datetime helper objects before returning
            clean_legs = []
            for leg in parsed_legs:
                l_copy = dict(leg)
                l_copy.pop("_dep_dt", None)
                l_copy.pop("_arr_dt", None)
                clean_legs.append(l_copy)

            total_duration = (
                int(it.get("duration") / 60)
                if it.get("duration") is not None
                else None
            )

            parsed_itineraries.append({
                "duration_minutes": total_duration,
                "departure_time": _format_dt(start_dt),
                "arrival_time": _format_dt(end_dt),
                "transfers": it.get("transfers", 0),
                "legs": clean_legs,
            })

        logger.info(f"[Transitous] Parsed itinerary count: {len(parsed_itineraries)}")

        if not parsed_itineraries:
            logger.info("[Transitous] Coverage/status: NO_ITINERARY")
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                note="Transitous returned empty or unparseable itineraries.",
            )

        logger.info(f"[Transitous] Coverage/status: SUCCESS ({len(parsed_itineraries)} itineraries)")
        return ProviderResult(
            status=ProviderStatus.SUCCESS,
            provider_name=self.provider_name,
            itineraries=parsed_itineraries,
        )
