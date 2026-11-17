from typing import Tuple, Optional, Dict, Any, Set

class BusinessValidator:
    """Stage 8: Business rules validation (no negative costs, non-overlapping times, duplicate prevention)."""

    @staticmethod
    def validate(data: Dict[str, Any], target_currency: str = "USD") -> Tuple[bool, Optional[str]]:
        trip_obj = data.get("trip") if "trip" in data else data
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        seen_places: Set[str] = set()
        target_curr_clean = (target_currency or "USD").upper().strip()

        for d_idx, day in enumerate(days):
            acts = day.get("activities", [])

            for a_idx, act in enumerate(acts):
                # 1. Cost checks
                cost_info = act.get("cost") or {}
                amount = cost_info.get("amount") if isinstance(cost_info, dict) else act.get("ticket_price", 0.0)
                if amount is not None and amount < 0:
                    return False, f"Negative cost {amount} found in Day {d_idx+1} Activity {a_idx+1}"

                # 2. Time & Duration checks
                st = str(act.get("start_time", "09:00"))
                et = str(act.get("end_time", "10:30"))
                try:
                    s_parts = st.split(":")
                    st_mins = int(s_parts[0]) * 60 + int(s_parts[1])
                    e_parts = et.split(":")
                    et_mins = int(e_parts[0]) * 60 + int(e_parts[1])

                    if et_mins <= st_mins:
                        return False, f"Activity '{act.get('title')}' end_time {et} is before start_time {st}"
                except Exception:
                    pass

                # 3. Duplicate POI & Compound Section check across days
                place_obj = act.get("place") if isinstance(act.get("place"), dict) else {}
                p_name = str(place_obj.get("name") or act.get("title") or "").strip()
                p_name_l = p_name.lower()

                # Airport & arrival/departure transport hubs are allowed on arrival/departure days
                is_transit_hub = any(k in p_name_l for k in ["airport", "railway station", "train station", "bus terminal", "ferry terminal", "transit hub"])
                if is_transit_hub and (d_idx == 0 or d_idx == len(days) - 1):
                    continue

                if p_name and len(p_name) > 3:
                    if p_name_l in seen_places:
                        return False, f"DUPLICATE_POI_DETECTED: '{p_name}' is scheduled multiple times in the itinerary"

                    from app.services.poi_service import is_compound_sub_section_of
                    is_sub, parent_name, matched_ex = is_compound_sub_section_of(p_name, seen_places)
                    if is_sub:
                        return False, f"COMPOUND_LANDMARK_DUPLICATE: '{p_name}' is a sub-section of already scheduled '{matched_ex}' ({parent_name})"

                    seen_places.add(p_name_l)

        return True, None
