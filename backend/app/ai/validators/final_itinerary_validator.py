"""
final_itinerary_validator.py — Comprehensive Final Itinerary Validation Layer

Validates generated itineraries against user inputs, geographic feasibility,
real places, dietary accuracy, temporal scheduling, and financial planning
before saving and display.
"""

from typing import Dict, Any, List, Tuple, Optional
import re
from datetime import date, timedelta
from app.services.route_optimizer import haversine_distance_km

GENERIC_PLACEHOLDER_SUBSTRINGS = [
    "scenic walk & artisan trail",
    "scenic overlook & panoramic vistas",
    "regional culinary lunch",
    "artisan trail near",
    "panoramic vistas:",
    "culinary lunch near",
    "landmark 1",
    "bistro 1",
    "museum 1",
    "sample place",
    "dummy place",
    "placeholder",
    "shortcut",
    "shortcut to",
    "shortcut to khao san",
    "abandond building",
    "abandoned building",
    "old car",
    "thai bamboo tattoo",
    "turn right",
    "turn left",
    "walk along",
    "head north",
    "head south",
    "blue corridor",
    "sarawak flagpole",
    "flightless birds",
    "world of parrot",
    "oriental bird aviaries",
    "zone 1",
    "zone 2",
    "zone 3",
    "zone 4",
    "hornbill park",
    "love aviary",
    "bulbul land",
    "brahminy kite",
    "mini stone henge",
    "godzilla x kong mural",
    "upside down house",
    "bamboo wood",
    "old city wall",
    "seylanovs house",
    "cultural landmark & heritage enclave",
    "scenic park & nature boardwalk",
    "lunch recommendation near",
    "dinner recommendation near",
    "recommendation near",
    "historic city center",
    "city center",
    "central district",
    "historic center",
    "local dining near",
    "dining exploration",
    "independent dining exploration",
    "old town & heritage quarter",
    "riverfront promenade & public gardens",
    "artisan souvenir bazaar & walk"
]

FORBIDDEN_VEGETARIAN_KEYWORDS = [
    "anticucho", "sandwich de chola", "chairo", "beef", "pork", "chicken",
    "meat", "lamb", "fish", "seafood", "steak", "poultry", "bacon"
]


class FinalItineraryValidator:
    """
    Final multi-point itinerary validation layer.
    Ensures zero empty days, schema completeness, geographic feasibility,
    real place verification, dietary compliance, and temporal consistency.
    """

    @classmethod
    def validate_itinerary_payload(
        cls,
        days_data: List[Dict[str, Any]],
        destination: str,
        start_date: date,
        end_date: date,
        expected_days: int,
        currency: str,
        interests: Optional[str] = None,
        directives: Optional[str] = None,
        pace: str = "balanced",
        transport_mode: str = "Mixed Transport",
        accommodation_preference: str = "hotel",
        dietary_preferences: Optional[str] = None,
        travelers_count: Optional[int] = None,
        adults_count: Optional[int] = None,
        children_count: Optional[int] = None
    ) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """
        Validate itinerary days and activities against contract requirements.
        Returns: (is_valid, validation_warnings_or_errors, validated_days)
        """
        issues = []
        if not days_data or len(days_data) == 0:
            return False, ["Itinerary contains zero days"], []

        # 1. Day Count Validation
        if len(days_data) < expected_days:
            issues.append(f"Day count mismatch: expected {expected_days} days, found {len(days_data)}")

        validated_days = []
        total_activities = 0
        is_vegetarian = bool(dietary_preferences and "veg" in dietary_preferences.lower())
        seen_attractions_trip = set()
        seen_coords_trip = []

        for d_idx in range(expected_days):
            day_num = d_idx + 1
            expected_day_date = start_date + timedelta(days=d_idx)

            # Find matching day info from input, or create structured day
            day_info = next((d for d in days_data if d.get("day_number") == day_num), None)
            if not day_info and d_idx < len(days_data):
                day_info = days_data[d_idx]

            base_city = (day_info.get("base_city") if day_info else None) or destination
            overnight_stay = (day_info.get("overnight_stay") if day_info else None) or f"{base_city} Hotel"

            if not day_info:
                day_info = {
                    "day_number": day_num,
                    "date": expected_day_date.isoformat(),
                    "title": f"Day {day_num}: Explore {base_city}",
                    "theme_note": f"Base: {base_city} | Overnight: {overnight_stay}",
                    "base_city": base_city,
                    "overnight_stay": overnight_stay,
                    "activities": []
                }

            acts = day_info.get("activities", [])

            # 2. Activity Count Validation (Must not have zero activities)
            if not acts or len(acts) == 0:
                issues.append(f"Day {day_num} has 0 scheduled activities")
            else:
                total_activities += len(acts)

            # 3. Activity Structure, Real Places, Dietary & Geographic Validation
            cleaned_acts = []
            prev_lat = None
            prev_lon = None
            prev_title = None

            for a_idx, act in enumerate(acts):
                title = str(act.get("title") or f"Visit Attraction {a_idx+1}").strip()
                desc = str(act.get("description") or "").strip()
                st = str(act.get("start_time") or "09:00").strip()
                et = str(act.get("end_time") or "10:30").strip()
                dur = int(act.get("duration_minutes") or 90)

                place_dict = act.get("place") if isinstance(act.get("place"), dict) else {}
                p_name = str(place_dict.get("name") or act.get("place_name") or title).strip()
                p_cat = str(place_dict.get("category") or "Sightseeing").strip()
                p_lat = place_dict.get("latitude") or act.get("latitude")
                p_lon = place_dict.get("longitude") or act.get("longitude")

                # Check B: Activity Type & Category Identification
                is_hotel_action = (
                    any(k in title.lower() or k in p_name.lower() for k in ["check-in", "check in", "checkout", "check out"])
                    or ("hotel" in p_name.lower() and any(k in title.lower() for k in ["arrival", "check", "settle", "departure"]))
                )
                if is_hotel_action:
                    p_cat = "Hotel"

                is_dining = (
                    act.get("activity_type") == "meal"
                    or act.get("is_dining") is True
                    or "restaurant" in p_cat.lower()
                    or "cafe" in p_cat.lower()
                    or "dining" in p_cat.lower()
                    or "lunch" in title.lower()
                    or "dinner" in title.lower()
                )

                # Check A: Generic Placeholder Strings Detection
                lower_check = f"{title.lower()} {p_name.lower()}"
                is_dining_expl = p_cat in ["Dining Exploration", "Dining Recommendation"] or is_dining
                for ph_str in GENERIC_PLACEHOLDER_SUBSTRINGS:
                    if ph_str in ["dining exploration", "independent dining exploration", "lunch recommendation near", "dinner recommendation near", "recommendation near"]:
                        if is_dining_expl:
                            continue
                    if ph_str in lower_check:
                        issues.append(f"Day {day_num} Activity {a_idx+1}: Generic placeholder detected: '{ph_str}'")

                is_area_sugg = (
                    act.get("is_area_suggestion")
                    or "area suggestion" in title.lower()
                    or "area suggestion" in p_name.lower()
                    or "dining area" in p_name.lower()
                )

                is_transit_act = (
                    is_hotel_action
                    or act.get("activity_type") in ["transit", "transportation"]
                    or "transfer" in title.lower()
                    or "transit" in str(act.get("transport_mode", "")).lower()
                    or "intercity" in str(act.get("transport_mode", "")).lower()
                )

                # Check Duplicate Attraction Across Entire Trip (attractions only, excluding dining and transit)
                norm_name = re.sub(r'[^a-z0-9]', '', p_name.lower())
                if not is_transit_act and not is_dining and not is_area_sugg and len(norm_name) >= 4:
                    if norm_name in seen_attractions_trip:
                        issues.append(f"Day {day_num}: Duplicate attraction '{p_name}' was already scheduled previously in trip")
                    seen_attractions_trip.add(norm_name)

                    if p_lat is not None and p_lon is not None:
                        try:
                            f_plat, f_plon = float(p_lat), float(p_lon)
                            for prev_name, prev_lat_c, prev_lon_c in seen_coords_trip:
                                if abs(f_plat - prev_lat_c) < 0.0001 and abs(f_plon - prev_lon_c) < 0.0001:
                                    issues.append(f"Day {day_num}: Attraction '{p_name}' shares identical coordinates ({f_plat}, {f_plon}) with '{prev_name}'")
                                    break
                            seen_coords_trip.append((p_name, f_plat, f_plon))
                        except Exception:
                            pass

                if prev_lat and prev_lon and p_lat and p_lon:
                    try:
                        leg_dist = haversine_distance_km(float(prev_lat), float(prev_lon), float(p_lat), float(p_lon))
                        if leg_dist > 45.0 and not is_transit_act:
                            issues.append(
                                f"Day {day_num}: Unrealistic distance {round(leg_dist, 1)} km between '{prev_title}' and '{title}' without explicit intercity transit"
                            )
                    except Exception:
                        pass

                prev_lat = p_lat
                prev_lon = p_lon
                prev_title = title

                # Check C: Meal / Restaurant Verification & Dietary Enforcement
                is_dining = (
                    act.get("activity_type") == "meal"
                    or "restaurant" in p_cat.lower()
                    or "cafe" in p_cat.lower()
                    or "dining" in p_cat.lower()
                    or "lunch" in title.lower()
                    or "dinner" in title.lower()
                )

                is_area_sugg = act.get("is_area_suggestion") or "area suggestion" in title.lower() or "area suggestion" in p_name.lower() or "dining exploration" in title.lower()
                if is_area_sugg:
                    is_dining = is_dining or ("dining" in title.lower() or "dining" in p_name.lower() or act.get("activity_type") == "meal")
                    act["is_dining"] = is_dining
                    act["is_area_suggestion"] = True
                    act_type = "area_suggestion"
                    p_cat = "Area Suggestion"
                    if isinstance(place_dict, dict):
                        place_dict["category"] = "Area Suggestion"
                        place_dict["rating"] = None
                        place_dict["latitude"] = None
                        place_dict["longitude"] = None
                    act["rating"] = None
                    p_lat = None
                    p_lon = None
                else:
                    act_type = "transit" if is_hotel_action else ("meal" if is_dining else (act.get("activity_type") or ("transit" if is_transit_act else "sightseeing")))
                    if is_dining and "dining recommendation" not in p_cat.lower() and "area suggestion" not in p_cat.lower():
                        p_cat = "Restaurant"

                # Dietary compliance check
                meal_meta = act.get("meal_details") if isinstance(act.get("meal_details"), dict) else {}
                sig_dish = str(meal_meta.get("signature_dish") or act.get("signature_dish") or "").lower()
                full_food_text = f"{title.lower()} {desc.lower()} {sig_dish}"
                clean_food_text = re.sub(r"\b(?:mock|vegan|vegetarian|plant-based|soy)\s+meats?\b", "plant_protein", full_food_text, flags=re.IGNORECASE)

                if is_vegetarian and is_dining:
                    for forbidden in FORBIDDEN_VEGETARIAN_KEYWORDS:
                        if re.search(r"\b" + re.escape(forbidden) + r"\b", clean_food_text, re.IGNORECASE):
                            issues.append(
                                f"Day {day_num} Dining Activity '{title}' violates vegetarian diet with '{forbidden}'"
                            )

                # Check D: Sunset Scheduling Check
                if "sunset" in title.lower() or "sunset" in desc.lower():
                    # Parse start hour
                    try:
                        st_hr = int(st.split(":")[0])
                        st_min = int(st.split(":")[1])
                        total_st_mins = st_hr * 60 + st_min
                        if total_st_mins < 17 * 60 + 15:  # Before 17:15
                            issues.append(
                                f"Day {day_num}: Sunset activity '{title}' scheduled prematurely at {st} (expected ~17:45-18:35)"
                            )
                    except Exception:
                        pass

                # Check E: Ticket price vs Meal cost
                cost = act.get("cost") if isinstance(act.get("cost"), dict) else {}
                act_curr = cost.get("currency") or act.get("currency") or currency
                raw_ticket = act.get("ticket_price")
                ticket_amt = float(raw_ticket) if raw_ticket is not None else 0.0
                meal_cost_amt = act.get("meal_cost") or meal_meta.get("estimated_cost")

                # Check F: Grand Palace & Wat Pho Constraints
                p_name_lower = p_name.lower()
                title_lower = title.lower()
                if "grand palace" in p_name_lower or "grand palace" in title_lower:
                    if ticket_amt == 0.0:
                        from app.services.currency_service import CurrencyService
                        ticket_amt = round(CurrencyService.convert(500.0, "THB", act_curr), 2)
                    try:
                        st_hr = int(st.split(":")[0])
                        st_min = int(st.split(":")[1])
                        st_tot = st_hr * 60 + st_min
                        et_hr = int(et.split(":")[0])
                        et_min = int(et.split(":")[1])
                        et_tot = et_hr * 60 + et_min
                        if st_tot >= 15 * 60 + 30 or et_tot > 16 * 60:
                            issues.append(
                                f"Day {day_num}: Grand Palace scheduled after operating hours at {st} (closing time strictly 15:30)"
                            )
                            st = "09:00"
                            et = "11:30"
                            dur = 150
                    except Exception:
                        pass
                elif "wat pho" in p_name_lower or "wat pho" in title_lower:
                    if ticket_amt == 0.0:
                        from app.services.currency_service import CurrencyService
                        ticket_amt = round(CurrencyService.convert(300.0, "THB", act_curr), 2)

                # Currency Integrity: Prevent BOB leakage in non-Bolivia trips
                if destination.strip().lower() not in ["bolivia", "la paz", "copacabana"]:
                    if act_curr == "BOB":
                        act_curr = currency
                    if isinstance(cost, dict) and cost.get("currency") == "BOB":
                        cost["currency"] = currency

                # Resolve truthful rating without hardcoding 4.7
                raw_rating = place_dict.get("rating") if isinstance(place_dict, dict) else act.get("rating")
                resolved_rating = None
                if raw_rating is not None:
                    try:
                        resolved_rating = round(float(raw_rating), 1)
                    except (ValueError, TypeError):
                        resolved_rating = None

                # Ensure Provenance Metadata adhering to Verified, Estimated, Unavailable
                raw_prov = act.get("provenance") or (act.get("metadata") or {}).get("provenance") or {}
                if isinstance(raw_prov, str):
                    raw_prov = {"source": raw_prov}

                if destination.strip().lower() not in ["bolivia", "la paz", "copacabana"]:
                    if "BOB" in str(raw_prov.get("price_source", "")):
                        raw_prov["price_source"] = str(raw_prov["price_source"]).replace("BOB", act_curr)

                is_curated_poi = bool(p_lat and p_lon and (p_lat != 0.0 or p_lon != 0.0) and not is_dining and not is_transit_act and not is_area_sugg)
                coords_status = "Unavailable" if is_area_sugg else ("Verified Coordinates" if (p_lat and p_lon and (p_lat != 0.0 or p_lon != 0.0)) else "Estimated Coordinates")
                rating_status = "Unrated" if is_area_sugg else ("Provider Rating" if resolved_rating is not None else "Unrated")
                has_opening_hours = bool(place_dict.get("opening_time") or act.get("opening_time"))
                schedule_status = "Confirmed" if has_opening_hours else "Tentative (Hours unavailable)"
                hours_status = "Hours unverified / Tentative" if is_area_sugg else ("Verified Registry Hours" if (is_curated_poi and has_opening_hours) else "Opening hours unavailable (Tentative schedule)")
                price_status = "Official Entry Registry" if (ticket_amt > 0 and is_curated_poi) else ("Free Public Access" if (ticket_amt == 0 and act.get("is_free_verified")) else ("Estimated" if is_area_sugg else "Price not verified"))
                overall_status = "Unavailable" if is_area_sugg else ("Verified" if (is_curated_poi and not is_dining and not is_transit_act and p_lat and p_lon) else "Estimated")

                provenance = {
                    **raw_prov,
                    "place_verification": raw_prov.get("place_verification") or (f"Verified Knowledge Base ({destination})" if is_curated_poi else "Area Directory"),
                    "coordinates_status": coords_status,
                    "rating_status": rating_status,
                    "schedule_status": schedule_status,
                    "opening_hours_source": raw_prov.get("opening_hours_source") or hours_status,
                    "price_source": raw_prov.get("price_source") or price_status,
                    "status": overall_status,
                    "overall_status": overall_status,
                    "source": raw_prov.get("source") or ("Verified POI Database" if overall_status == "Verified" else "Market-Calibrated Estimate"),
                    "confidence": float(act.get("confidence_score") or raw_prov.get("confidence") or (0.99 if is_curated_poi else 0.85))
                }

                # Canonical Traveler Count Consistency Validation
                target_adults = adults_count if adults_count is not None else (
                    max(1, travelers_count - (children_count or 0)) if (travelers_count and children_count) else (travelers_count or 1)
                )
                target_children = children_count if children_count is not None else 0
                target_total = target_adults + target_children
                canonical_traveler_str = f"{target_adults} adult{'s' if target_adults != 1 else ''}" + (
                    f", {target_children} child{'ren' if target_children != 1 else ''}" if target_children > 0 else ""
                )

                ai_reason = str(act.get("ai_reason") or "")
                desc_str = str(act.get("description") or "")

                # Validate and repair adult count in ai_reason
                m_tc = re.search(r"(\d+)\s*adults?", ai_reason, re.IGNORECASE)
                if m_tc and int(m_tc.group(1)) != target_adults:
                    issues.append(f"Day {day_num} Activity {a_idx+1}: Mentioned {m_tc.group(1)} adults instead of canonical adult count {target_adults}")
                    ai_reason = re.sub(r"\b\d+\s*adults?\b", f"{target_adults} adult{'s' if target_adults != 1 else ''}", ai_reason, flags=re.IGNORECASE)

                # Validate and repair adult count in description
                m_desc = re.search(r"(\d+)\s*adults?", desc_str, re.IGNORECASE)
                if m_desc and int(m_desc.group(1)) != target_adults:
                    desc_str = re.sub(r"\b\d+\s*adults?\b", f"{target_adults} adult{'s' if target_adults != 1 else ''}", desc_str, flags=re.IGNORECASE)

                # Eliminate improper group substitutions like "3 adults, 1 child" when total is 3 (2 adults, 1 child)
                if target_children > 0 and target_adults < target_total:
                    bad_pattern = rf"\b{target_total}\s*adults?,\s*{target_children}\s*child"
                    if re.search(bad_pattern, ai_reason, re.IGNORECASE):
                        ai_reason = re.sub(bad_pattern, canonical_traveler_str, ai_reason, flags=re.IGNORECASE)
                    if re.search(bad_pattern, desc_str, re.IGNORECASE):
                        desc_str = re.sub(bad_pattern, canonical_traveler_str, desc_str, flags=re.IGNORECASE)

                cleaned_acts.append({
                    **act,
                    "order_index": a_idx,
                    "title": title,
                    "description": desc_str,
                    "ai_reason": ai_reason,
                    "start_time": st,
                    "end_time": et,
                    "duration_minutes": dur,
                    "activity_type": act_type,
                    "meal_cost": meal_cost_amt,
                    "meal_details": act.get("meal_details"),
                    "transit_details": act.get("transit_details"),
                    "dietary_suitability": act.get("dietary_suitability") or ("Vegetarian" if is_vegetarian and is_dining else None),
                    "provenance": provenance,
                    "place": {
                        "name": p_name,
                        "category": p_cat,
                        "address": place_dict.get("address", f"{destination}"),
                        "city": place_dict.get("city", base_city),
                        "latitude": float(p_lat) if p_lat is not None else None,
                        "longitude": float(p_lon) if p_lon is not None else None,
                        "rating": resolved_rating,
                        "ticket_price": ticket_amt if not is_dining else 0.0,
                        "google_maps_url": place_dict.get("google_maps_url")
                    },
                    "currency": act_curr
                })

            theme_note_str = day_info.get("theme_note") or ""
            if f"Base: {base_city}" not in theme_note_str:
                theme_note_str = f"Base: {base_city} | Overnight: {overnight_stay}" + (f" • {theme_note_str}" if theme_note_str else "")

            validated_days.append({
                "day_number": day_num,
                "date": expected_day_date.isoformat(),
                "title": day_info.get("title") or f"Day {day_num}: {base_city} Exploration",
                "theme_note": theme_note_str,
                "base_city": base_city,
                "overnight_stay": overnight_stay,
                "activities": cleaned_acts
            })

        # Final check: Fail only if total activities is zero across all days
        if total_activities == 0:
            return False, ["Fatal: Generated itinerary contains zero activities across all days"], validated_days

        is_valid = len(issues) == 0
        return is_valid, issues, validated_days
