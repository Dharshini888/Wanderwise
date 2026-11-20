import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

def optimize_routes(origin, destination, preferred_mode, budget):
    # Legacy function for V1 compatibility
    return [{"mode": "Transport"}]

logger = logging.getLogger(__name__)
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

from datetime import datetime, timedelta, date, timezone
import uuid
import re
import math
from .station_normalizer import normalize_station_name, normalize_mode_name
from .tz_utils import KOLKATA_TZ
from ..maps.osrm_service import haversine_distance

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """
    Normalizes, validates, and optimizes multimodal routes.
    """

    @staticmethod
    def _normalize_provider_time(
        time_str: Optional[str],
        journey_date_str: Optional[str] = None,
        target_base_date: Optional[date] = None,
        reference_departure_time: Optional[Any] = None,
    ) -> Optional[datetime]:
        if not time_str or time_str in ["Unavailable", "None", "null"]:
            return None

        t_clean = str(time_str).strip()

        # Determine target base date
        base_date = target_base_date
        if not base_date and journey_date_str:
            j_lower = str(journey_date_str).strip().lower()
            if j_lower in ("tomorrow", "next day"):
                base_date = datetime.now().date() + timedelta(days=1)
            elif j_lower in ("today", "now"):
                base_date = datetime.now().date()
            else:
                try:
                    if "T" in journey_date_str:
                        base_date = datetime.fromisoformat(journey_date_str.replace("Z", "+00:00")).date()
                    else:
                        base_date = datetime.strptime(journey_date_str.split()[0], "%Y-%m-%d").date()
                except Exception:
                    pass

        if not base_date:
            base_date = datetime.now().date()

        # 1. Direct ISO format check
        try:
            parsed_iso = datetime.fromisoformat(t_clean.replace("Z", "+00:00"))
            # Preserve genuine next-day / midnight-crossing departures (base_date + 1 or + 2 days)
            if target_base_date:
                iso_date = parsed_iso.date()
                if iso_date == base_date:
                    return parsed_iso
                elif iso_date in (base_date + timedelta(days=1), base_date + timedelta(days=2)):
                    # Genuine next-day departure returned by provider (e.g. Transitous / MOTIS)
                    return parsed_iso
                elif iso_date < base_date:
                    # Stale query date; align time to base_date
                    return parsed_iso.replace(year=base_date.year, month=base_date.month, day=base_date.day)
                elif iso_date > base_date + timedelta(days=3):
                    # Out of range future date; align time to base_date
                    return parsed_iso.replace(year=base_date.year, month=base_date.month, day=base_date.day)
            return parsed_iso
        except Exception:
            pass

        # 2. Try parsing 12-hour or 24-hour time strings
        t_obj = None
        for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S", "%I:%M:%S %p", "%H.%M"]:
            try:
                t_obj = datetime.strptime(t_clean, fmt).time()
                break
            except Exception:
                continue

        if not t_obj:
            return None

        # Midnight-crossing detection for bare times:
        # If reference departure is late evening (hour >= 20) and service is early morning (hour < 6),
        # this service departs after midnight on the next calendar day.
        final_date = base_date
        if target_base_date and reference_departure_time:
            ref_hour = None
            if isinstance(reference_departure_time, datetime):
                ref_hour = reference_departure_time.hour
            elif isinstance(reference_departure_time, str):
                try:
                    ref_hour = datetime.fromisoformat(reference_departure_time.replace("Z", "+00:00")).hour
                except Exception:
                    for fmt in ["%H:%M", "%I:%M %p", "%I:%M%p"]:
                        try:
                            ref_hour = datetime.strptime(reference_departure_time.strip(), fmt).hour
                            break
                        except Exception:
                            pass
            if ref_hour is not None and ref_hour >= 20 and t_obj.hour < 6:
                final_date = base_date + timedelta(days=1)

        return datetime.combine(final_date, t_obj)

    @staticmethod
    def normalize_route(
        provider: str,
        mode: str,
        raw_itinerary: Dict[str, Any],
        origin_name: str,
        dest_name: str,
        default_dist: float,
        journey_date: Optional[str] = None,
        departure_time: Optional[Any] = None,
        origin_lat: Optional[float] = None,
        origin_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Converts a provider itinerary into the common normalized schema.
        Returns None if the route is hopelessly invalid or terminates in the wrong destination.
        """
        route_id = raw_itinerary.get("route_id") or raw_itinerary.get("journey_id") or str(uuid.uuid4())
        
        legs = raw_itinerary.get("legs", [])

        # Validate destination identity if coordinates are available
        if provider not in ("OSRM", "Driving") and legs and dest_lat is not None and dest_lon is not None:
            last_l = legs[-1]
            last_to_loc = last_l.get("to_loc") or {}
            last_alighting = last_l.get("alighting_stop") or {}
            term_lat = last_to_loc.get("lat") or last_alighting.get("lat") or last_l.get("to_lat")
            term_lon = last_to_loc.get("lon") or last_alighting.get("lon") or last_l.get("to_lon")
            if term_lat is not None and term_lon is not None:
                end_drift_km = haversine_distance(float(term_lat), float(term_lon), float(dest_lat), float(dest_lon))
                if end_drift_km > 50.0:
                    logger.warning(
                        f"[ROUTE_OPTIMIZER] REJECTED: Itinerary from {provider} terminates at "
                        f"({term_lat}, {term_lon}) which is {end_drift_km:.1f} km from requested destination '{dest_name}'."
                    )
                    return None

        # 1. Distance
        dist_km = raw_itinerary.get("distance_km") or raw_itinerary.get("distance")
        if dist_km is None or dist_km <= 0:
            dist_km = default_dist

        # 2. Resolve Target Base Date
        target_date = None
        if departure_time:
            if isinstance(departure_time, datetime):
                target_date = departure_time.date()
            elif isinstance(departure_time, str):
                try:
                    target_date = datetime.fromisoformat(departure_time.replace("Z", "+00:00")).date()
                except Exception:
                    pass
        if not target_date and journey_date:
            j_str = str(journey_date).strip().lower()
            if j_str in ("tomorrow", "next day"):
                target_date = datetime.now().date() + timedelta(days=1)
            elif j_str in ("today", "now"):
                target_date = datetime.now().date()
            else:
                try:
                    target_date = datetime.strptime(j_str.split()[0], "%Y-%m-%d").date()
                except Exception:
                    pass
        if not target_date:
            target_date = datetime.now().date()

        # 3. Departure and Arrival Parsing (Truth-First)
        raw_dep_str = raw_itinerary.get("departure_time")
        raw_arr_str = raw_itinerary.get("arrival_time")

        if legs and (not raw_dep_str or not raw_arr_str):
            first_leg = legs[0]
            last_leg = legs[-1]
            if not raw_dep_str:
                raw_dep_str = first_leg.get("departure_time")
            if not raw_arr_str:
                raw_arr_str = last_leg.get("arrival_time")

        dep_dt = RouteOptimizer._normalize_provider_time(raw_dep_str, journey_date, target_base_date=target_date, reference_departure_time=departure_time)
        arr_dt = RouteOptimizer._normalize_provider_time(raw_arr_str, journey_date, target_base_date=target_date, reference_departure_time=departure_time)

        provider_dur_min = raw_itinerary.get("duration_minutes") or raw_itinerary.get("duration_min")
        dur_min = provider_dur_min
        dur_source = f"{provider}"
        is_overnight = False

        is_flight_route = (provider == "FlightProvider") or ((raw_itinerary.get("mode") or mode or "").lower() in ("flight", "commercial flight"))

        if not is_flight_route:
            if dep_dt:
                if dep_dt.tzinfo is not None:
                    dep_dt = dep_dt.astimezone(KOLKATA_TZ)
                else:
                    dep_dt = dep_dt.replace(tzinfo=KOLKATA_TZ)
                dep_dt = dep_dt.replace(second=0, microsecond=0)

            if arr_dt:
                if arr_dt.tzinfo is not None:
                    arr_dt = arr_dt.astimezone(KOLKATA_TZ)
                else:
                    arr_dt = arr_dt.replace(tzinfo=KOLKATA_TZ)
                arr_dt = arr_dt.replace(second=0, microsecond=0)
        else:
            # Preserve authentic origin and destination airport local timezones
            if dep_dt:
                dep_dt = dep_dt.replace(second=0, microsecond=0)
            if arr_dt:
                arr_dt = arr_dt.replace(second=0, microsecond=0)

        if dep_dt and arr_dt:
            # Duration calculation in UTC across any international timezone boundary
            dep_utc = dep_dt.astimezone(timezone.utc) if dep_dt.tzinfo else dep_dt.replace(tzinfo=timezone.utc)
            arr_utc = arr_dt.astimezone(timezone.utc) if arr_dt.tzinfo else arr_dt.replace(tzinfo=timezone.utc)

            # Overnight adjustment: if arrival time <= departure time in UTC, add +1 day
            if arr_utc <= dep_utc:
                arr_dt += timedelta(days=1)
                arr_utc += timedelta(days=1)
                is_overnight = True
            elif arr_dt.date() > dep_dt.date():
                is_overnight = True

            calc_min = (arr_utc - dep_utc).total_seconds() / 60.0
            if calc_min > 0:
                dur_min = round(calc_min, 1)
                dur_source = f"{provider} (Calculated from timestamps)"
            elif dur_min and float(dur_min) > 0:
                dur_rounded = int(round(float(dur_min)))
                arr_dt = (dep_dt + timedelta(minutes=dur_rounded)).replace(second=0, microsecond=0)
                dur_min = float(dur_rounded)
            else:
                dur_min = max(1.0, calc_min if calc_min > 0 else 5.0)
                dur_rounded = int(round(dur_min))
                arr_dt = (dep_dt + timedelta(minutes=dur_rounded)).replace(second=0, microsecond=0)
                dur_min = float(dur_rounded)
        elif dep_dt is None and departure_time:
            if isinstance(departure_time, datetime):
                dep_dt = departure_time.astimezone(KOLKATA_TZ) if departure_time.tzinfo else departure_time.replace(tzinfo=KOLKATA_TZ)
            elif isinstance(departure_time, str):
                dep_dt = RouteOptimizer._normalize_provider_time(departure_time, journey_date, target_base_date=target_date)
                if dep_dt and not is_flight_route:
                    dep_dt = dep_dt.astimezone(KOLKATA_TZ) if dep_dt.tzinfo else dep_dt.replace(tzinfo=KOLKATA_TZ)

            if dep_dt and dur_min and float(dur_min) > 0:
                dur_rounded = int(round(float(dur_min)))
                dep_dt = dep_dt.replace(second=0, microsecond=0)
                arr_dt = (dep_dt + timedelta(minutes=dur_rounded)).replace(second=0, microsecond=0)
                dur_min = float(dur_rounded)
                dur_source = f"{provider}"
                is_overnight = arr_dt.date() > dep_dt.date()
        elif dep_dt and arr_dt is None and dur_min and float(dur_min) > 0:
            dur_rounded = int(round(float(dur_min)))
            dep_dt = dep_dt.replace(second=0, microsecond=0)
            arr_dt = (dep_dt + timedelta(minutes=dur_rounded)).replace(second=0, microsecond=0)
            dur_min = float(dur_rounded)
            dur_source = f"{provider}"
            is_overnight = arr_dt.date() > dep_dt.date()

        # Truncate seconds to zero for clean minute-level consistency
        if dep_dt:
            dep_dt = dep_dt.replace(second=0, microsecond=0)
        if arr_dt:
            arr_dt = arr_dt.replace(second=0, microsecond=0)

        # Ensure duration is always positive
        if dur_min is not None:
            dur_min = max(1.0, float(dur_min))
        else:
            dur_min = 10.0

        # Format display strings — prefer authentic provider displays with timezones
        dep_time_iso = dep_dt.isoformat() if dep_dt else None
        arr_time_iso = arr_dt.isoformat() if arr_dt else None

        prov_dep_display = raw_itinerary.get("departure_time_display")
        prov_arr_display = raw_itinerary.get("arrival_time_display")

        if prov_dep_display and prov_dep_display not in ("Unavailable", "None", None):
            dep_display = prov_dep_display
        elif dep_dt:
            tz_str = dep_dt.tzname() if is_flight_route else ""
            dep_display = f"{dep_dt.strftime('%I:%M %p').lstrip('0')} {tz_str or ''}".strip()
        else:
            dep_display = "Unavailable"

        if prov_arr_display and prov_arr_display not in ("Unavailable", "None", None):
            arr_display_base = prov_arr_display
        elif arr_dt:
            tz_str = arr_dt.tzname() if is_flight_route else ""
            arr_display_base = f"{arr_dt.strftime('%I:%M %p').lstrip('0')} {tz_str or ''}".strip()
        else:
            arr_display_base = "Unavailable"

        arr_display = arr_display_base
        if is_overnight and "(+1 day)" not in arr_display:
            arr_display = f"{arr_display_base} (+1 day)"

        # 4. Sources & Verification Terminology
        geometry = raw_itinerary.get("geometry", [])
        geometry_source = f"{provider} Geometry" if geometry else "Schematic"
        distance_source = f"{provider}" if raw_itinerary.get("distance_km") else "Fallback"
        fare = raw_itinerary.get("fare")
        fare_val = fare if isinstance(fare, (int, float)) and fare > 0 else None
        fare_source = f"{provider} Verified" if fare_val else "Fare unavailable"

        verification_status = "Estimated"
        if provider == "RailRadar":
            verification_status = "Provider Verified"
        elif provider in ["GTFSLocal", "GTFS", "Transitous"]:
            verification_status = "Schedule Verified"
        elif provider == "FlightProvider":
            verification_status = "Partially Verified"
        elif provider == "Transitland":
            verification_status = "Transit Data Verified"
        elif provider == "OSRM":
            verification_status = "Route Calculated"
        else:
            verification_status = "VERIFIED" if raw_itinerary.get("verified", True) else "ESTIMATED"

        walking_m = raw_itinerary.get("walking_distance_m")
        transfers = raw_itinerary.get("transfers", 0)

        is_flight_route = (provider == "FlightProvider") or ((raw_itinerary.get("mode") or mode or "").lower() in ("flight", "commercial flight"))

        # English-normalized Names
        if is_flight_route:
            # Never overwrite flight origin or destination with railway station names
            norm_orig = origin_name
            norm_dest = dest_name
            dep_station = raw_itinerary.get("origin_airport") or raw_itinerary.get("departure_station") or norm_orig
            arr_station = raw_itinerary.get("destination_airport") or raw_itinerary.get("arrival_station") or norm_dest
        else:
            norm_orig = normalize_station_name(origin_name)
            norm_dest = normalize_station_name(dest_name)
            dep_station = normalize_station_name(raw_itinerary.get("departure_station") or norm_orig)
            arr_station = normalize_station_name(raw_itinerary.get("arrival_station") or norm_dest)

        norm_mode = normalize_mode_name(raw_itinerary.get("mode") or mode)

        # Build clean legs with English normalization
        clean_legs = []
        for leg in legs:
            c_leg = dict(leg)
            if is_flight_route:
                # Retain authentic airport names and endpoints on flight journey legs
                f_name = c_leg.get("from_name") or c_leg.get("from_stop") or norm_orig
                t_name = c_leg.get("to_name") or c_leg.get("to_stop") or norm_dest
                if f_name.lower().endswith(" junction"):
                    f_name = f_name[:-9].strip()
                if t_name.lower().endswith(" junction"):
                    t_name = t_name[:-9].strip()
                c_leg["from_name"] = f_name
                c_leg["to_name"] = t_name
            else:
                f_stop = c_leg.get("boarding_stop", {}).get("name") if isinstance(c_leg.get("boarding_stop"), dict) else c_leg.get("boarding_stop")
                t_stop = c_leg.get("alighting_stop", {}).get("name") if isinstance(c_leg.get("alighting_stop"), dict) else c_leg.get("alighting_stop")
                c_leg["from_name"] = normalize_station_name(c_leg.get("from_name") or c_leg.get("from_stop") or f_stop or norm_orig)
                c_leg["to_name"] = normalize_station_name(c_leg.get("to_name") or c_leg.get("to_stop") or t_stop or norm_dest)
            if "mode" in c_leg:
                c_leg["mode"] = normalize_mode_name(c_leg["mode"])
            if "geometry" not in c_leg:
                c_leg["geometry"] = []
            clean_legs.append(c_leg)

        # If all legs are walking, label the route mode Walking
        if clean_legs and all("walk" in (l.get("mode") or "").lower() for l in clean_legs):
            norm_mode = "Walking"

        dep_source = "user_selected" if (raw_dep_str is None and departure_time) else (provider if dep_dt else None)
        arr_source = "calculated_from_provider_duration" if (raw_arr_str is None and arr_dt) else (provider if arr_dt else None)

        route_verification = raw_itinerary.get("verification") or {
            "level": "PARTIALLY_VERIFIED" if provider == "FlightProvider" else ("route_calculated" if provider == "OSRM" else ("scheduled" if provider in ("RailRadar", "GTFSLocal", "GTFS", "Transitous") else "realtime_verified")),
            "provider": provider,
            "live": bool((raw_itinerary.get("realtime") or {}).get("available")),
        }

        route_source = raw_itinerary.get("source") or {
            "schedule": provider if provider != "OSRM" else None,
            "duration": dur_source,
            "distance": distance_source,
            "fare": fare_source,
            "departure": dep_source,
            "arrival": arr_source,
            "live_tracking": "SCHEDULE DATA ONLY" if provider in ("RailRadar", "GTFSLocal", "GTFS", "Transitous") else "UNAVAILABLE",
        }

        # 5. Build Normalized Object
        return {
            "route_id": route_id,
            "provider": provider,
            "mode": norm_mode,
            "origin": norm_orig,
            "destination": norm_dest,
            "distance_km": round(float(dist_km), 2) if dist_km else None,
            "distance_source": distance_source,
            "duration_min": round(float(dur_min), 1),
            "duration_minutes": round(float(dur_min), 1),
            "duration_source": dur_source,
            "verification_status": verification_status,
            "fare": fare_val,
            "fare_source": fare_source,
            "walking_distance_m": walking_m,
            "transfers": transfers,
            "legs": clean_legs,
            "geometry": geometry,
            "geometry_source": geometry_source,
            
            "departure_time": dep_time_iso,
            "arrival_time": arr_time_iso,
            "departure_time_display": dep_display,
            "arrival_time_display": arr_display,
            "departure_source": dep_source,
            "arrival_source": arr_source,
            "is_overnight": is_overnight,

            "verification": route_verification,
            "source": route_source,
            "realtime": raw_itinerary.get("realtime") or {"available": False, "status": "unavailable"},

            "is_long_distance_fallback": raw_itinerary.get("is_long_distance_fallback", False),
            
            # Optional extra fields for RailRadar / GTFS
            "train_number": raw_itinerary.get("train_number"),
            "train_name": raw_itinerary.get("train_name"),
            "departure_station": dep_station,
            "arrival_station": arr_station,
            "operating_days": raw_itinerary.get("operating_days", []),
            "intermediate_stops": raw_itinerary.get("intermediate_stops", []),
            "scheduled_status": raw_itinerary.get("scheduled_status"),
            "live_status": raw_itinerary.get("live_status"),
            "delay_min": raw_itinerary.get("delay_min"),
            "current_station": raw_itinerary.get("current_station"),
            "next_station": raw_itinerary.get("next_station"),
            "platform": raw_itinerary.get("platform"),

            # Optional extra fields for FlightProvider
            "flight_number": raw_itinerary.get("flight_number"),
            "airline": raw_itinerary.get("airline") or raw_itinerary.get("airline_name"),
            "airline_name": raw_itinerary.get("airline_name") or raw_itinerary.get("airline"),
            "origin_iata": raw_itinerary.get("origin_iata"),
            "destination_iata": raw_itinerary.get("destination_iata"),
            "origin_airport": raw_itinerary.get("origin_airport"),
            "destination_airport": raw_itinerary.get("destination_airport"),
            "origin_lat": raw_itinerary.get("origin_lat"),
            "origin_lon": raw_itinerary.get("origin_lon"),
            "destination_lat": raw_itinerary.get("destination_lat"),
            "destination_lon": raw_itinerary.get("destination_lon"),
            "flight_departure_time": raw_itinerary.get("flight_departure_time"),
            "flight_arrival_time": raw_itinerary.get("flight_arrival_time"),
            "flight_departure_time_display": raw_itinerary.get("flight_departure_time_display"),
            "flight_arrival_time_display": raw_itinerary.get("flight_arrival_time_display"),
            "flight_duration_minutes": raw_itinerary.get("flight_duration_minutes"),
            "flight_duration_display": raw_itinerary.get("flight_duration_display"),
            "flight_distance_km": raw_itinerary.get("flight_distance_km"),
            "total_duration_minutes": raw_itinerary.get("total_duration_minutes"),
            "total_duration_display": raw_itinerary.get("total_duration_display"),
            "total_distance_km": raw_itinerary.get("total_distance_km"),
            "duration_breakdown": raw_itinerary.get("duration_breakdown"),
            "is_door_to_door": raw_itinerary.get("is_door_to_door", False),
        }

    @staticmethod
    def optimize(routes: List[Dict[str, Any]], request_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Takes a list of normalized routes and returns categorized optimal routes.
        All optimization is deterministic — no AI for factual metrics.
        Excludes already-departed services from recommended selections.
        """
        if not routes:
            return {}

        valid_routes = [r for r in routes if not r.get("is_long_distance_fallback")]
        if not valid_routes:
            valid_routes = routes

        def is_service_departed(r: Dict[str, Any]) -> bool:
            if not request_time:
                return False
            dep_iso = r.get("departure_time")
            if not dep_iso:
                return False
            try:
                d = datetime.fromisoformat(dep_iso.replace("Z", "+00:00"))
                n = request_time
                if d.tzinfo is not None and n.tzinfo is None:
                    n = n.replace(tzinfo=d.tzinfo)
                elif d.tzinfo is None and n.tzinfo is not None:
                    d = d.replace(tzinfo=n.tzinfo)
                # Evaluates strictly against full timezone-aware timestamps (never bare time strings)
                if d < n:
                    return True
            except Exception:
                pass
            return False

        # Pool of non-departed candidates for recommendations
        candidate_pool = [r for r in valid_routes if not is_service_departed(r)]
        if not candidate_pool:
            candidate_pool = valid_routes

        # 1. Fastest — minimum valid total journey duration from catchable candidates
        fastest = min(candidate_pool, key=lambda x: x["duration_min"])

        # 2. Cheapest — only verified fares
        with_fare = [r for r in candidate_pool if r.get("fare") is not None and r["fare"] > 0]
        cheapest = min(with_fare, key=lambda x: x["fare"]) if with_fare else None

        # 3. Least Walking — only verified walking distances
        with_walking = [r for r in candidate_pool if r.get("walking_distance_m") is not None]
        least_walking = min(with_walking, key=lambda x: x["walking_distance_m"]) if with_walking else None

        # 4. Safest — best connection safety (fewest RED/YELLOW, shortest total waiting)
        #    Based on verification_status and transfer count (proxy for connection risk)
        VERIFIED = {"Provider Verified", "Schedule Verified", "VERIFIED", "PROVIDER_VERIFIED", "SCHEDULE_VERIFIED"}
        def safety_score(r):
            vs = r.get("verification_status", "")
            v_penalty = 0 if vs in VERIFIED else 50
            transfers = r.get("transfers") or 0
            waiting = r.get("total_waiting_time_min") or 0
            return v_penalty + transfers * 10 + waiting
        safest = min(candidate_pool, key=safety_score)
        if safest:
            safest["strategy_reason"] = "Lowest transfer risk, verified schedule, and minimal station waiting time."

        # 5. Greenest — lowest distance (proxy for CO₂) + transit preference over driving/flying
        def green_score(r):
            dist = r.get("distance_km") or 9999
            # OSRM Driving and flight penalized heavily vs. public transit
            mode = (r.get("mode") or "").lower()
            prov = r.get("provider") or ""
            is_road = prov == "OSRM" or "road" in mode or "driv" in mode
            is_flight = prov == "FlightProvider" or "flight" in mode or "air" in mode
            mode_penalty = 300 if is_flight else (150 if is_road else 0)
            return dist + mode_penalty
        greenest = min(candidate_pool, key=green_score)
        if greenest:
            greenest["strategy_reason"] = "Lowest environmental impact, prioritizing electrified rail and public transit over road and air travel."

        # 6. Fewest Transfers
        fewest_transfers = min(candidate_pool, key=lambda x: (x.get("transfers") or 0, x["duration_min"]))

        # 7. Best Overall Scoring: Fair, deterministic, weighted across all factors
        # Scoring factors (lower = better):
        #   base: total journey duration (minutes)
        #   transfers: +15 per transfer (encourages fewer connections)
        #   waiting: +0.5 per waiting minute (mild wait penalty)
        #   verification bonus: -20 for verified public transit (trust quality)
        #   osrm_road_penalty: +30 when rail/verified transit exists (don't auto-prefer road)
        #   fallback_penalty: +5000 for long-distance road fallback
        has_verified_transit = any(
            r.get("provider") not in ("OSRM",)
            and r.get("verification_status") in ("Provider Verified", "Schedule Verified")
            for r in candidate_pool
        )

        def score_route(r):
            dur = r["duration_min"]
            trans = (r.get("transfers") or 0) * 15
            waiting = (r.get("total_waiting_time_min") or 0) * 0.5

            v_stat = r.get("verification_status", "")
            if v_stat in VERIFIED:
                v_bonus = -20   # Verified public transit preferred
            elif v_stat == "Route Calculated":
                v_bonus = 10
            else:
                v_bonus = 0

            # Apply OSRM road penalty when verified public transit is available
            # This prevents OSRM from auto-winning Best Overall
            osrm_penalty = 30 if (r.get("provider") == "OSRM" and has_verified_transit) else 0
            fallback_penalty = 5000 if r.get("is_long_distance_fallback") else 0
            return dur + trans + waiting + v_bonus + osrm_penalty + fallback_penalty

        best_overall = min(candidate_pool, key=score_route)

        # Deterministic why_this_route generation
        why_this_route = []
        p_name = best_overall.get("provider")

        if p_name in ("RailRadar", "Indian Railways Timetable", "IndianRailways-ScheduleVerified"):
            prov_label = "RailRadar" if p_name == "RailRadar" else "Indian Railways Timetable"
            why_this_route.append(f"Scheduled railway route verified by {prov_label}")
            if best_overall.get("train_name"):
                why_this_route.append(f"Train: {best_overall['train_name']} ({best_overall.get('train_number', '')})")
            why_this_route.append("Station-specific departure and arrival available")
            why_this_route.append("Duration calculated from station timestamps")
        elif p_name == "OSRM":
            why_this_route.append("Shortest calculated road duration")
            why_this_route.append("Exact route geometry available")
            why_this_route.append("Duration source: OSRM (Reported)")
        elif p_name == "FlightProvider":
            why_this_route.append("Verified flight route for long-distance journey")
            why_this_route.append("Duration from flight provider schedule")
        else:
            if fastest and best_overall["route_id"] == fastest["route_id"]:
                why_this_route.append("Shortest verified duration among comparable routes.")
            if best_overall.get("transfers", 0) == 0:
                why_this_route.append("Direct journey with no transfers.")
            if best_overall.get("verification_status") in VERIFIED:
                why_this_route.append(f"Provider: {p_name} verified schedule.")

        def get_dep_sort_key(r):
            dep_iso = r.get("departure_time")
            if not dep_iso:
                return (1, datetime.max.replace(tzinfo=KOLKATA_TZ))
            try:
                dt = datetime.fromisoformat(dep_iso.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=KOLKATA_TZ)
                return (0, dt)
            except Exception:
                return (1, datetime.max.replace(tzinfo=KOLKATA_TZ))

        sorted_routes = sorted(routes, key=get_dep_sort_key)

        return {
            "recommended_route": best_overall,
            "route_options": sorted_routes,
            "fastest_route": fastest,
            "cheapest_route": cheapest,
            "least_walking_route": least_walking,
            "safest_route": safest,
            "greenest_route": greenest,
            "fewest_transfers_route": fewest_transfers,
            "best_overall_route": best_overall,
            "optimization": {
                "strategy": "best_overall",
                "selected_route_id": best_overall["route_id"],
                "why_this_route": why_this_route,
            },
        }


