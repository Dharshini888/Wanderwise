import uuid
from typing import Dict, Any, List
from app.core.currencies import get_currency_info
from app.services.poi_service import fetch_real_pois_for_destination, get_google_maps_search_url
from app.services.route_optimizer import estimate_travel_transition, optimize_daily_route

class Normalizer:
    """Stage 9: Data Normalization (Real place names, Google Maps URLs, transition details, duration calculations)."""

    @staticmethod
    def normalize(data: Dict[str, Any], currency_code: str = "USD") -> Dict[str, Any]:
        curr_info = get_currency_info(currency_code)

        trip_obj = data.get("trip") if "trip" in data else data
        dest = str(trip_obj.get("destination") or "Destination").strip()
        country = str(trip_obj.get("country") or "").strip()
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        # Fetch verified real POIs for fallback
        real_pois = fetch_real_pois_for_destination(dest, country)

        normalized_days = []
        for d_idx, day in enumerate(days):
            day_num = day.get("day_number", d_idx + 1)
            day_title = str(day.get("title", f"Day {day_num}")).strip()
            theme_note = str(day.get("theme_note", "Cultural exploration & sightseeing")).strip()

            raw_acts = day.get("activities", [])
            if not raw_acts:
                opt_pois = optimize_daily_route(real_pois)
                time_slots = [
                    ("08:30", "09:30", "morning", 60),
                    ("09:45", "11:45", "morning", 120),
                    ("12:00", "13:15", "afternoon", 75),
                    ("13:30", "16:00", "afternoon", 150),
                    ("16:30", "18:30", "evening", 120)
                ]
                raw_acts = []
                for p_idx, poi in enumerate(opt_pois[:5]):
                    st, et, slot, dur_m = time_slots[min(p_idx, len(time_slots) - 1)]
                    p_name = poi["name"]
                    p_cat = poi["category"]
                    cat_l = p_cat.lower()

                    if "restaurant" in cat_l or "cafe" in cat_l:
                        t_title = f"🍽️ Lunch at {p_name}" if "12:" in st else f"☕ Breakfast at {p_name}"
                    elif "viewpoint" in cat_l or "observation" in cat_l:
                        t_title = f"🌆 {p_name} Sunset Vistas"
                    elif "museum" in cat_l:
                        t_title = f"🏛️ Tour {p_name}"
                    else:
                        t_title = f"📍 Explore {p_name}"

                    raw_acts.append({
                        "id": f"act_d{day_num}_{p_idx+1:02d}",
                        "start_time": st,
                        "end_time": et,
                        "duration_minutes": dur_m,
                        "time_slot": slot,
                        "title": t_title,
                        "description": poi.get("description") or f"Explore {p_name}, a top-rated destination in {dest}.",
                        "place": poi,
                        "cost": {
                            "amount": poi.get("ticket_price", 0.0),
                            "currency": poi.get("currency", currency_code),
                            "symbol": curr_info.get("symbol", "$"),
                            "estimated": False
                        },
                        "ticket_price": poi.get("ticket_price", 0.0),
                        "transport_mode": "Walking",
                        "weather_suitability": "Mixed",
                        "crowd_level": poi.get("crowd", "Moderate"),
                        "ai_reason": poi.get("ai_reason") or f"✓ Fits schedule\n✓ Walking distance\n✓ 4.7★ reviews",
                        "confidence_score": poi.get("confidence", 0.96)
                    })

            def parse_start(a):
                st = str(a.get("start_time", "09:00"))
                try:
                    p = st.split(":")
                    return int(p[0]) * 60 + int(p[1])
                except Exception:
                    return 9 * 60

            sorted_acts = sorted(raw_acts, key=parse_start)
            norm_acts = []

            for a_idx, act in enumerate(sorted_acts):
                st_str = str(act.get("start_time", "09:00")).strip()
                et_str = str(act.get("end_time", "10:30")).strip()

                # Duration
                dur_mins = act.get("duration_minutes")
                try:
                    s_p = st_str.split(":")
                    e_p = et_str.split(":")
                    s_m = int(s_p[0]) * 60 + int(s_p[1])
                    e_m = int(e_p[0]) * 60 + int(e_p[1])
                    if e_m > s_m:
                        dur_mins = e_m - s_m
                    else:
                        dur_mins = 90
                except Exception:
                    dur_mins = 90

                # Time slot
                time_slot_val = act.get("time_slot")
                if not time_slot_val or str(time_slot_val).lower() not in ["morning", "afternoon", "evening", "night"]:
                    try:
                        hr = int(st_str.split(":")[0])
                        if 6 <= hr < 12:
                            time_slot_val = "morning"
                        elif 12 <= hr < 17:
                            time_slot_val = "afternoon"
                        elif 17 <= hr < 21:
                            time_slot_val = "evening"
                        else:
                            time_slot_val = "night"
                    except Exception:
                        time_slot_val = "morning"

                # Place object
                place_raw = act.get("place")
                if isinstance(place_raw, dict):
                    p_name = str(place_raw.get("name") or act.get("title") or "Attraction").strip()
                    p_cat = str(place_raw.get("category") or "Sightseeing").strip()
                    p_addr = str(place_raw.get("address") or f"{dest}").strip()
                    p_lat = place_raw.get("latitude") or place_raw.get("lat") or 35.6762
                    p_lon = place_raw.get("longitude") or place_raw.get("lng") or 139.6503
                    p_rating = place_raw.get("rating", 4.7)
                    p_open = place_raw.get("opening_time", "08:00 AM")
                    p_close = place_raw.get("closing_time", "10:00 PM")
                    p_sig = place_raw.get("signature_dish")
                    p_near = place_raw.get("nearby", [])
                else:
                    p_name = str(act.get("place_name") or act.get("title") or "Attraction").strip()
                    p_cat = "Sightseeing"
                    p_addr = f"{dest}"
                    p_lat = 35.6762
                    p_lon = 139.6503
                    p_rating = 4.7
                    p_open = "08:00 AM"
                    p_close = "10:00 PM"
                    p_sig = None
                    p_near = []

                g_maps_url = get_google_maps_search_url(p_name, p_addr)

                # Cost object
                cost_raw = act.get("cost")
                if isinstance(cost_raw, dict):
                    amt = float(cost_raw.get("amount") or 0.0)
                    c_code = str(cost_raw.get("currency") or currency_code).upper()
                    c_sym = str(cost_raw.get("symbol") or curr_info.get("symbol", "$"))
                    c_est = bool(cost_raw.get("estimated", False))
                else:
                    amt = float(act.get("ticket_price") or 0.0)
                    c_code = currency_code.upper()
                    c_sym = curr_info.get("symbol", "$")
                    c_est = False

                # Travel Transition calculation with next activity
                t_mode = act.get("transport_mode") or "Walking"
                t_dur = act.get("transport_duration") or "8 mins"
                t_dist = act.get("distance") or "0.6 km"
                next_place_name = act.get("next_place_name") or ""

                if a_idx < len(sorted_acts) - 1:
                    next_act = sorted_acts[a_idx + 1]
                    n_place = next_act.get("place") if isinstance(next_act.get("place"), dict) else {}
                    n_lat = n_place.get("latitude") or 35.6762
                    n_lon = n_place.get("longitude") or 139.6503
                    next_place_name = str(n_place.get("name") or next_act.get("title") or "").strip()

                    trans = estimate_travel_transition(float(p_lat), float(p_lon), float(n_lat), float(n_lon))
                    t_mode = trans["travel_mode"]
                    t_dur = trans["travel_time"]
                    t_dist = trans["distance"]

                # Ensure tips is a clean List[str]
                raw_tips = act.get("metadata", {}).get("tips") if isinstance(act.get("metadata"), dict) else None
                if not raw_tips:
                    raw_tips = [place_raw.get("tip") or f"Visit early to enjoy a quiet atmosphere at {p_name}."] if isinstance(place_raw, dict) else [f"Visit early for scenic views at {p_name}."]
                elif isinstance(raw_tips, str):
                    raw_tips = [raw_tips]

                norm_act = {
                    "id": act.get("id") or f"act_d{day_num}_{a_idx+1:02d}",
                    "start_time": st_str,
                    "end_time": et_str,
                    "duration_minutes": int(dur_mins),
                    "time_slot": time_slot_val,
                    "title": str(act.get("title") or f"Visit {p_name}").strip(),
                    "description": str(act.get("description") or f"Explore {p_name} in {dest}.").strip(),
                    "next_place_name": next_place_name,
                    "place": {
                        "name": p_name,
                        "category": p_cat,
                        "address": p_addr,
                        "city": dest,
                        "country": country,
                        "latitude": float(p_lat),
                        "longitude": float(p_lon),
                        "rating": float(p_rating),
                        "opening_time": p_open,
                        "closing_time": p_close,
                        "signature_dish": p_sig,
                        "nearby": p_near,
                        "google_maps_url": g_maps_url
                    },
                    "cost": {
                        "amount": float(amt),
                        "currency": c_code,
                        "symbol": c_sym,
                        "estimated": c_est
                    },
                    "ticket_price": float(amt),
                    "transport_mode": t_mode,
                    "transport_duration": t_dur,
                    "distance": t_dist,
                    "weather_suitability": str(act.get("weather_suitability") or "Mixed").strip(),
                    "crowd_level": str(act.get("crowd_level") or "Moderate").strip(),
                    "ai_reason": str(act.get("ai_reason") or f"✓ Fits schedule\n✓ Walking distance\n✓ Highly rated").strip(),
                    "confidence_score": float(act.get("confidence_score") or 0.96),
                    "is_locked": bool(act.get("is_locked", False)),
                    "metadata": {
                        "tips": raw_tips,
                        "things_to_carry": "Comfortable footwear & camera",
                        "photo_rating": float(p_rating),
                        "nearby": p_near,
                        "signature_dish": p_sig,
                        "rain_backup": f"Indoor exhibition at {p_name}"
                    }
                }
                norm_acts.append(norm_act)

            normalized_days.append({
                "day_number": day_num,
                "title": day_title,
                "theme_note": theme_note,
                "activities": norm_acts
            })

        result = dict(data)
        if "trip" in result:
            result["trip"]["itinerary_days"] = normalized_days
            result["trip"]["version"] = "2.2"
            result["trip"]["currency"] = currency_code
            result["trip"]["currency_code"] = currency_code
        else:
            result["itinerary_days"] = normalized_days
            result["version"] = "2.2"
            result["currency"] = currency_code
            result["currency_code"] = currency_code


        return result
