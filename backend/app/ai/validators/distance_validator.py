from typing import Tuple, Optional, Dict, Any
from app.services.route_optimizer import haversine_distance_km

class DistanceValidator:
    """Stage 6: Geographic Distance & Realistic Travel Speed Validator."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        trip_obj = data.get("trip") if "trip" in data else data
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        for d_idx, day in enumerate(days):
            acts = day.get("activities", [])
            for i in range(len(acts) - 1):
                curr_act = acts[i]
                next_act = acts[i + 1]

                c_place = curr_act.get("place") if isinstance(curr_act.get("place"), dict) else {}
                n_place = next_act.get("place") if isinstance(next_act.get("place"), dict) else {}

                c_lat = c_place.get("latitude") or curr_act.get("latitude")
                c_lon = c_place.get("longitude") or curr_act.get("longitude")
                n_lat = n_place.get("latitude") or next_act.get("latitude")
                n_lon = n_place.get("longitude") or next_act.get("longitude")

                if c_lat and c_lon and n_lat and n_lon:
                    try:
                        dist_km = haversine_distance_km(float(c_lat), float(c_lon), float(n_lat), float(n_lon))
                        is_transit = (
                            curr_act.get("activity_type") in ["transit", "transportation"]
                            or next_act.get("activity_type") in ["transit", "transportation"]
                            or "transfer" in str(curr_act.get("title", "")).lower()
                            or "transfer" in str(next_act.get("title", "")).lower()
                            or "intercity" in str(curr_act.get("transport_mode", "")).lower()
                            or "intercity" in str(next_act.get("transport_mode", "")).lower()
                        )
                        # If distance > 45 km without an explicit scheduled intercity transfer block, reject
                        if dist_km > 45.0 and not is_transit:
                            return False, f"DISTANCE_VIOLATION: Unrealistic travel distance {dist_km} km between '{curr_act.get('title')}' and '{next_act.get('title')}' on Day {d_idx+1} without an explicit intercity transit leg"
                        elif dist_km > 650.0:
                            return False, f"DISTANCE_VIOLATION: Intercity transfer distance {dist_km} km exceeds single-day limit between '{curr_act.get('title')}' and '{next_act.get('title')}' on Day {d_idx+1}"
                    except Exception:
                        pass

        return True, None
