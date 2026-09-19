from typing import Tuple, Optional, Dict, Any

class OpeningHoursValidator:
    """Stage 5: Operating Days & Opening Hours Validation Layer."""

    @staticmethod
    def _time_to_minutes(t_str: str, is_closing: bool = False) -> int:
        try:
            if not t_str:
                return -1
            s = str(t_str).strip().upper()
            if is_closing and s in ["00:00", "0:00", "24:00", "12:00 AM", "MIDNIGHT"]:
                return 1440  # Midnight end-of-day

            is_pm = "PM" in s
            is_am = "AM" in s
            clean_s = s.replace("AM", "").replace("PM", "").strip()
            parts = clean_s.split(":")
            hr = int(parts[0])
            mn = int(parts[1]) if len(parts) > 1 else 0

            if is_pm and hr < 12:
                hr += 12
            elif is_am and hr == 12:
                hr = 0
            elif is_closing and hr == 0 and mn == 0:
                return 1440

            return hr * 60 + mn
        except Exception:
            return -1

    @classmethod
    def parse_hours(cls, raw_open: Optional[str], raw_close: Optional[str]) -> Tuple[int, int, str, str]:
        open_s = str(raw_open).strip() if raw_open else ""
        close_s = str(raw_close).strip() if raw_close else ""

        if ("-" in open_s or " TO " in open_s.upper()) and (not close_s or close_s == open_s):
            sep = "-" if "-" in open_s else (" TO " if " TO " in open_s.upper() else "to")
            parts = open_s.split(sep, 1)
            open_s = parts[0].strip()
            close_s = parts[1].strip()

        op_m = cls._time_to_minutes(open_s, is_closing=False)
        cl_m = cls._time_to_minutes(close_s, is_closing=True)

        return op_m, cl_m, open_s, close_s

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        trip_obj = data.get("trip") if "trip" in data else data
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        for d_idx, day in enumerate(days):
            acts = day.get("activities", [])
            for a_idx, act in enumerate(acts):
                st_mins = cls._time_to_minutes(act.get("start_time", "09:00"))
                et_mins = cls._time_to_minutes(act.get("end_time", "10:30"), is_closing=True)

                place_info = act.get("place") if isinstance(act.get("place"), dict) else {}
                meta = act.get("metadata") if isinstance(act.get("metadata"), dict) else {}

                open_time_str = place_info.get("opening_time") or meta.get("opening_time") or place_info.get("opening_hours") or meta.get("opening_hours")
                close_time_str = place_info.get("closing_time") or meta.get("closing_time")

                if open_time_str:
                    op_mins, cl_mins, clean_open, clean_close = cls.parse_hours(open_time_str, close_time_str)

                    if op_mins != -1 and cl_mins != -1:
                        if cl_mins <= op_mins:
                            cl_mins += 1440

                        # Allow 30 min flexibility
                        if st_mins < op_mins - 30 or et_mins > cl_mins + 30:
                            # Deterministic adjustment if within reasonable bound (within 2 hours)
                            if st_mins < op_mins and (op_mins - st_mins) <= 120:
                                dur = et_mins - st_mins if et_mins > st_mins else 60
                                new_st_hr, new_st_mn = op_mins // 60, op_mins % 60
                                new_et_mins = min(op_mins + dur, cl_mins)
                                new_et_hr, new_et_mn = (new_et_mins % 1440) // 60, (new_et_mins % 1440) % 60
                                act["start_time"] = f"{new_st_hr:02d}:{new_st_mn:02d}"
                                act["end_time"] = f"{new_et_hr:02d}:{new_et_mn:02d}"
                                continue
                            elif et_mins > cl_mins and (et_mins - cl_mins) <= 120:
                                new_et_mins = cl_mins
                                new_et_hr, new_et_mn = (new_et_mins % 1440) // 60, (new_et_mins % 1440) % 60
                                act["end_time"] = f"{new_et_hr:02d}:{new_et_mn:02d}"
                                continue

                            p_name = place_info.get("name") or act.get("title")
                            return False, f"OPENING_HOURS_VIOLATION: '{p_name}' operates ({clean_open}-{clean_close}), but scheduled ({act.get('start_time')}-{act.get('end_time')}) on Day {d_idx+1}"

        return True, None
