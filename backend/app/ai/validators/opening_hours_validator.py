from typing import Tuple, Optional, Dict, Any

class OpeningHoursValidator:
    """Stage 5: Operating Days & Opening Hours Validation Layer."""

    @staticmethod
    def _time_to_minutes(t_str: str) -> int:
        try:
            s = str(t_str).strip().upper()
            is_pm = "PM" in s
            is_am = "AM" in s
            clean_s = s.replace("AM", "").replace("PM", "").strip()
            parts = clean_s.split(":")
            hr = int(parts[0])
            mn = int(parts[1])
            if is_pm and hr < 12:
                hr += 12
            elif is_am and hr == 12:
                hr = 0
            return hr * 60 + mn
        except Exception:
            return -1

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        trip_obj = data.get("trip") if "trip" in data else data
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        for d_idx, day in enumerate(days):
            acts = day.get("activities", [])
            for a_idx, act in enumerate(acts):
                st_mins = cls._time_to_minutes(act.get("start_time", "09:00"))
                et_mins = cls._time_to_minutes(act.get("end_time", "10:30"))

                place_info = act.get("place") if isinstance(act.get("place"), dict) else {}
                meta = act.get("metadata") if isinstance(act.get("metadata"), dict) else {}

                open_time_str = place_info.get("opening_time") or meta.get("opening_time")
                close_time_str = place_info.get("closing_time") or meta.get("closing_time")

                if open_time_str and close_time_str:
                    op_mins = cls._time_to_minutes(open_time_str)
                    cl_mins = cls._time_to_minutes(close_time_str)

                    if op_mins != -1 and cl_mins != -1:
                        # Allow 30 min flexibility
                        if st_mins < op_mins - 30 or et_mins > cl_mins + 30:
                            p_name = place_info.get("name") or act.get("title")
                            return False, f"OPENING_HOURS_VIOLATION: '{p_name}' operates ({open_time_str}-{close_time_str}), but scheduled ({act.get('start_time')}-{act.get('end_time')}) on Day {d_idx+1}"

        return True, None
