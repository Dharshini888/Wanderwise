import json
import re
from app.ai.providers.base_provider import BaseAIProvider
from app.services.poi_service import fetch_real_pois_for_destination, get_google_maps_search_url
from app.services.route_optimizer import optimize_daily_route, estimate_travel_transition
from app.ai.validators.opening_hours_validator import OpeningHoursValidator

class MockProvider(BaseAIProvider):
    """Mock AI Provider returning realistic schedules and rich destination POIs."""

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        dest = "Tokyo"
        dest_match = re.search(r"Destination:\s*([^\n,]+)", prompt)
        if dest_match:
            dest = dest_match.group(1).strip()

        curr_code = "USD"
        curr_symbol = "$"
        if "INR" in prompt:
            curr_code = "INR"
            curr_symbol = "₹"
        elif "EUR" in prompt:
            curr_code = "EUR"
            curr_symbol = "€"
        elif "JPY" in prompt:
            curr_code = "JPY"
            curr_symbol = "¥"

        total_days = 2
        match = re.search(r"Total Days:\s*(\d+)", prompt)
        if match:
            total_days = max(1, int(match.group(1)))

        all_pois = fetch_real_pois_for_destination(dest)

        days_list = []
        used_poi_names = set()

        time_slots = [
            ("08:30", "09:30", "morning", 60),
            ("09:45", "11:45", "morning", 120),
            ("12:00", "13:15", "afternoon", 75),
            ("13:30", "16:00", "afternoon", 150),
            ("16:30", "18:30", "evening", 120)
        ]

        pois_per_day = max(2, len(all_pois) // total_days)

        for d in range(1, total_days + 1):
            # Select unused POIs for this day
            available_pois = [p for p in all_pois if p["name"].lower() not in used_poi_names]
            if not available_pois:
                available_pois = all_pois

            ordered_day_pois = available_pois[:pois_per_day]

            # Track used POIs to prevent duplicates across days
            for p in ordered_day_pois:
                used_poi_names.add(p["name"].lower())

            acts = []
            for p_idx, poi in enumerate(ordered_day_pois):
                st, et, slot, dur_m = time_slots[min(p_idx, len(time_slots) - 1)]

                # Check opening time and align schedule start if needed
                op_str = poi.get("opening_time", "06:00 AM")
                op_mins = OpeningHoursValidator._time_to_minutes(op_str)
                st_mins = OpeningHoursValidator._time_to_minutes(st)

                if op_mins != -1 and st_mins < op_mins:
                    # Align start_time to opening_time
                    hr = op_mins // 60
                    mn = op_mins % 60
                    st = f"{hr:02d}:{mn:02d}"
                    et_m = op_mins + dur_m
                    hr_e = et_m // 60
                    mn_e = et_m % 60
                    et = f"{hr_e:02d}:{mn_e:02d}"

                p_name = poi["name"]
                p_addr = poi["address"]
                g_url = get_google_maps_search_url(p_name, p_addr)

                t_mode = "Walking"
                t_dur = "8 mins"
                t_dist = "0.6 km"
                next_place_name = ""

                if p_idx < len(ordered_day_pois) - 1:
                    next_p = ordered_day_pois[p_idx + 1]
                    next_place_name = next_p["name"]
                    trans = estimate_travel_transition(poi["latitude"], poi["longitude"], next_p["latitude"], next_p["longitude"])
                    t_mode = trans["travel_mode"]
                    t_dur = trans["travel_time"]
                    t_dist = trans["distance"]

                cat_lower = poi["category"].lower()
                if "restaurant" in cat_lower or "cafe" in cat_lower or "food" in cat_lower:
                    title_formatted = f"🍽️ Lunch at {p_name}" if "12:" in st else f"☕ Refreshments at {p_name}"
                elif "viewpoint" in cat_lower or "observation" in cat_lower:
                    title_formatted = f"🌆 {p_name} Sunset Vistas"
                elif "museum" in cat_lower:
                    title_formatted = f"🏛️ Tour {p_name}"
                else:
                    title_formatted = f"📍 Explore {p_name}"

                acts.append({
                    "id": f"act_mock_d{d}_{p_idx+1:02d}",
                    "start_time": st,
                    "end_time": et,
                    "duration_minutes": dur_m,
                    "time_slot": slot,
                    "title": title_formatted,
                    "description": poi.get("description") or f"Visit {p_name}, a top-rated destination in {dest}.",
                    "next_place_name": next_place_name,
                    "place": {
                        "name": p_name,
                        "category": poi["category"],
                        "address": p_addr,
                        "city": dest,
                        "country": "",
                        "latitude": poi["latitude"],
                        "longitude": poi["longitude"],
                        "rating": poi["rating"],
                        "opening_time": poi.get("opening_time", "06:00 AM"),
                        "closing_time": poi.get("closing_time", "10:00 PM"),
                        "signature_dish": poi.get("signature_dish"),
                        "nearby": poi.get("nearby", []),
                        "google_maps_url": g_url
                    },
                    "cost": {
                        "amount": float(poi.get("ticket_price", 0.0)),
                        "currency": poi.get("currency", curr_code),
                        "symbol": curr_symbol,
                        "estimated": False
                    },
                    "ticket_price": float(poi.get("ticket_price", 0.0)),
                    "transport_mode": t_mode,
                    "transport_duration": t_dur,
                    "distance": t_dist,
                    "weather_suitability": "Mixed",
                    "crowd_level": poi.get("crowd", "Moderate"),
                    "ai_reason": poi.get("ai_reason") or f"✓ Best visited in the morning\n✓ Walking distance\n✓ 4.7★ reviews",
                    "confidence_score": poi.get("confidence", 0.98),
                    "is_locked": False,
                    "metadata": {
                        "tips": [poi.get("tip") or f"Visit early to enjoy quiet atmosphere at {p_name}."],
                        "things_to_carry": "Comfortable footwear & camera",
                        "photo_rating": poi.get("rating", 4.8),
                        "nearby": poi.get("nearby", []),
                        "signature_dish": poi.get("signature_dish"),
                        "rain_backup": f"Indoor exhibition at {p_name}"
                    }
                })

            days_list.append({
                "day_number": d,
                "title": f"Day {d}: {dest} Heritage & Coastal Culture",
                "theme_note": f"Discover top historic landmarks, authentic dining & scenic viewpoints in {dest}",
                "activities": acts
            })

        return json.dumps({
            "trip": {
                "destination": dest,
                "version": "2.2",
                "itinerary_days": days_list
            }
        })
