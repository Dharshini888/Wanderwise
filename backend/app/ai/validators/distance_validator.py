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
                        # If distance > 40 km in a single city day transition, reject
                        if dist_km > 45.0:
                            return False, f"DISTANCE_VIOLATION: Unrealistic travel distance {dist_km} km between '{curr_act.get('title')}' and '{next_act.get('title')}' on Day {d_idx+1}"
                    except Exception:
                        pass

        return True, None
