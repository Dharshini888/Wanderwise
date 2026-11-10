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

from datetime import datetime, timedelta
import uuid
import re

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """
    Normalizes, validates, and optimizes multimodal routes.
    """

    @staticmethod
    def _normalize_provider_time(time_str: Optional[str], journey_date_str: Optional[str] = None) -> Optional[datetime]:
        if not time_str or time_str in ["Unavailable", "None", "null"]:
            return None

        t_clean = time_str.strip()

        # 1. Direct ISO format check
        try:
            return datetime.fromisoformat(t_clean.replace("Z", "+00:00"))
        except Exception:
            pass

        # 2. Try parsing 12-hour or 24-hour time strings
        t_obj = None
        for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S", "%I:%M:%S %p"]:
            try:
                t_obj = datetime.strptime(t_clean, fmt).time()
                break
            except Exception:
                continue

        if not t_obj:
            return None

        # 3. Determine base date
        base_date = None
        if journey_date_str:
            try:
                if "T" in journey_date_str:
                    base_date = datetime.fromisoformat(journey_date_str.replace("Z", "+00:00")).date()
                else:
                    base_date = datetime.strptime(journey_date_str.split()[0], "%Y-%m-%d").date()
            except Exception:
                pass

        if not base_date:
            base_date = datetime.now().date()

        return datetime.combine(base_date, t_obj)

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
    ) -> Optional[Dict[str, Any]]:
        """
        Converts a provider itinerary into the common normalized schema.
        Returns None if the route is hopelessly invalid.
        """
        route_id = str(uuid.uuid4())
        
        legs = raw_itinerary.get("legs", [])

        # 1. Distance
        dist_km = raw_itinerary.get("distance_km") or raw_itinerary.get("distance")
        if dist_km is None or dist_km <= 0:
            dist_km = default_dist

        # 2. Departure and Arrival Parsing (Truth-First)
        raw_dep_str = raw_itinerary.get("departure_time")
        raw_arr_str = raw_itinerary.get("arrival_time")

        if legs and (not raw_dep_str or not raw_arr_str):
            first_leg = legs[0]
            last_leg = legs[-1]
            if not raw_dep_str:
                raw_dep_str = first_leg.get("departure_time")
            if not raw_arr_str:
                raw_arr_str = last_leg.get("arrival_time")

        dep_dt = RouteOptimizer._normalize_provider_time(raw_dep_str, journey_date)
        arr_dt = RouteOptimizer._normalize_provider_time(raw_arr_str, journey_date)

        provider_dur_min = raw_itinerary.get("duration_minutes") or raw_itinerary.get("duration_min")
        dur_min = provider_dur_min
        dur_source = f"{provider}"
        is_overnight = False

        if dep_dt and arr_dt:
            # Overnight adjustment: if arrival time <= departure time, add +1 day
            if arr_dt <= dep_dt:
                arr_dt += timedelta(days=1)
                is_overnight = True

            calc_min = (arr_dt - dep_dt).total_seconds() / 60.0
            if calc_min > 0:
                dur_min = calc_min
                dur_source = f"{provider} (Calculated from timestamps)"
        elif dep_dt is None and departure_time:
            # If provider didn't specify a scheduled departure time (e.g. OSRM driving route),
            # but user/system supplied a departure time, use that departure time
            # and calculate arrival_time = departure_time + duration!
            if isinstance(departure_time, datetime):
                dep_dt = departure_time
            elif isinstance(departure_time, str):
                dep_dt = RouteOptimizer._normalize_provider_time(departure_time, journey_date)

            if dep_dt and dur_min and dur_min > 0:
                arr_dt = dep_dt + timedelta(minutes=float(dur_min))
                dur_source = f"{provider}"
                is_overnight = arr_dt.date() > dep_dt.date()
        elif dep_dt and arr_dt is None and dur_min and dur_min > 0:
            arr_dt = dep_dt + timedelta(minutes=float(dur_min))
            dur_source = f"{provider}"
            is_overnight = arr_dt.date() > dep_dt.date()

        # 3. Duration Validation
        if not dur_min or dur_min <= 0:
            logger.warning(f"[OPTIMIZER] Rejecting route from {provider}: invalid duration ({dur_min})")
            return None

        # Format display strings — prefer provider-supplied display strings over raw ISO
        dep_time_iso = dep_dt.isoformat() if dep_dt else None
        arr_time_iso = arr_dt.isoformat() if arr_dt else None

        # Use pre-formatted display strings from provider if available
        prov_dep_display = raw_itinerary.get("departure_time_display")
        prov_arr_display = raw_itinerary.get("arrival_time_display")

        if prov_dep_display and prov_dep_display not in ("Unavailable", "None", None):
            dep_display = prov_dep_display
        elif dep_dt:
            dep_display = dep_dt.strftime("%I:%M %p").lstrip("0")
        else:
            dep_display = "Unavailable"

        if prov_arr_display and prov_arr_display not in ("Unavailable", "None", None):
            arr_display_base = prov_arr_display
        elif arr_dt:
            arr_display_base = arr_dt.strftime("%I:%M %p").lstrip("0")
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
        fare_source = f"{provider} Verified" if fare_val else "Unavailable"

        verification_status = "Estimated"
        if provider == "RailRadar":
            verification_status = "Provider Verified"
        elif provider in ["GTFSLocal", "GTFS"]:
            verification_status = "Schedule Verified"
        elif provider == "Transitland":
            verification_status = "Transit Data Verified"
        elif provider == "OSRM":
            verification_status = "Provider Calculated"
        else:
            verification_status = "VERIFIED" if raw_itinerary.get("verified", True) else "ESTIMATED"

        walking_m = raw_itinerary.get("walking_distance_m")
        transfers = raw_itinerary.get("transfers", 0)

        # Build clean legs
        clean_legs = []
        for leg in legs:
            c_leg = dict(leg)
            if "geometry" not in c_leg:
                c_leg["geometry"] = []
            clean_legs.append(c_leg)

        dep_source = "user_selected" if (raw_dep_str is None and departure_time) else (provider if dep_dt else None)
        arr_source = "calculated_from_provider_duration" if (raw_arr_str is None and arr_dt) else (provider if arr_dt else None)

        # 5. Build Normalized Object
        return {
            "route_id": route_id,
            "provider": provider,
            "mode": mode,
            "origin": origin_name,
            "destination": dest_name,
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

            "verification": {
                "level": "provider_calculated" if provider == "OSRM" else ("scheduled" if provider in ("RailRadar", "GTFSLocal", "GTFS", "Transitous") else "realtime_verified"),
                "provider": provider,
                "live": False
            },
            "source": {
                "duration": dur_source,
                "distance": distance_source,
                "fare": fare_source,
                "departure": dep_source,
                "arrival": arr_source,
                "live_tracking": None
            },

            "is_long_distance_fallback": raw_itinerary.get("is_long_distance_fallback", False),
            
            # Optional extra fields for RailRadar / GTFS
            "train_number": raw_itinerary.get("train_number"),
            "train_name": raw_itinerary.get("train_name"),
            "departure_station": raw_itinerary.get("departure_station"),
            "arrival_station": raw_itinerary.get("arrival_station"),
            "operating_days": raw_itinerary.get("operating_days", []),
            "intermediate_stops": raw_itinerary.get("intermediate_stops", []),
            "scheduled_status": raw_itinerary.get("scheduled_status"),
            "live_status": raw_itinerary.get("live_status"),
            "delay_min": raw_itinerary.get("delay_min"),
            "current_station": raw_itinerary.get("current_station"),
            "next_station": raw_itinerary.get("next_station"),
            "platform": raw_itinerary.get("platform"),
        }

    @staticmethod
    def optimize(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a list of normalized routes and returns categorized optimal routes.
        All optimization is deterministic — no AI for factual metrics.
        """
        if not routes:
            return {}

        valid_routes = [r for r in routes if not r.get("is_long_distance_fallback")]
        if not valid_routes:
            valid_routes = routes

        # 1. Fastest — minimum valid total journey duration
        fastest = min(valid_routes, key=lambda x: x["duration_min"])

        # 2. Cheapest — only verified fares
        with_fare = [r for r in valid_routes if r.get("fare") is not None and r["fare"] > 0]
        cheapest = min(with_fare, key=lambda x: x["fare"]) if with_fare else None

        # 3. Least Walking — only verified walking distances
        with_walking = [r for r in valid_routes if r.get("walking_distance_m") is not None]
        least_walking = min(with_walking, key=lambda x: x["walking_distance_m"]) if with_walking else None

        # 4. Safest — best connection safety (fewest RED/YELLOW, shortest total waiting)
        #    Based on verification_status and transfer count (proxy for connection risk)
        VERIFIED = {"Provider Verified", "Schedule Verified", "VERIFIED"}
        def safety_score(r):
            vs = r.get("verification_status", "")
            v_penalty = 0 if vs in VERIFIED else 50
            transfers = r.get("transfers") or 0
            waiting = r.get("total_waiting_time_min") or 0
            return v_penalty + transfers * 10 + waiting
        safest = min(valid_routes, key=safety_score)

        # 5. Greenest — lowest distance (proxy for CO₂) + transit preference over driving
        def green_score(r):
            dist = r.get("distance_km") or 9999
            # Driving and flight penalized heavily vs. public transit
            mode = (r.get("mode") or "").lower()
            mode_penalty = 200 if ("flight" in mode or "road" in mode) else 0
            return dist + mode_penalty
        greenest = min(valid_routes, key=green_score)

        # 6. Fewest Transfers
        fewest_transfers = min(valid_routes, key=lambda x: (x.get("transfers") or 0, x["duration_min"]))

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
            for r in valid_routes
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

        best_overall = min(valid_routes, key=score_route)

        # Deterministic why_this_route generation
        why_this_route = []
        p_name = best_overall.get("provider")

        if p_name == "RailRadar":
            why_this_route.append("Scheduled railway route verified by RailRadar")
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

        return {
            "recommended_route": best_overall,
            "route_options": routes,
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


