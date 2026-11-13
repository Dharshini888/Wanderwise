import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.config.ai_config import ai_settings
from app.ai.providers.provider_factory import AIProviderFactory
from app.ai.prompt_loader import PromptLoader
from app.ai.validators.itinerary_validator import ItineraryValidator
from app.schemas.ai_response import AIResponse, AIResponseMetadata
from app.services.poi_service import fetch_real_pois_for_destination

class AIEngine:
    """Central AI Engine Orchestrator managing context building, prompt rendering, provider execution, retries, 5-stage validation, and response envelope generation."""

    def __init__(self):
        self.config = ai_settings

    def generate_trip(self, context_dict: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        destination = context_dict.get("destination", "Destination")
        country = context_dict.get("country") or destination
        total_days = int(context_dict.get("total_days") or context_dict.get("days") or 2)
        budget = float(context_dict.get("budget", 1000.0))
        curr_code = context_dict.get("currency_code") or context_dict.get("currency") or "USD"
        curr_symbol = context_dict.get("currency_symbol", "$")
        curr_country = context_dict.get("currency_country", country)
        activities_alloc = context_dict.get("activities_budget", round(budget * 0.15, 2))
        language = context_dict.get("language", "English")

        # Extract rich wizard details
        prefs = context_dict.get("trip_preferences") or {}
        travel_style = context_dict.get("travel_style") or prefs.get("travel_style") or "solo"
        travelers_dict = prefs.get("travelers") if isinstance(prefs.get("travelers"), dict) else {}
        children = int(context_dict.get("children") or prefs.get("children") or travelers_dict.get("children") or 0)
        raw_adults = context_dict.get("adults") or prefs.get("adults") or travelers_dict.get("adults")
        if raw_adults is not None:
            adults = int(raw_adults)
        else:
            raw_group = int(context_dict.get("group_size") or prefs.get("group_size") or 1)
            adults = max(1, raw_group - children)
        seniors = int(travelers_dict.get("seniors") or 0)
        pets = int(travelers_dict.get("pets") or 0)
        total_travelers = max(1, adults + children)
        group_size = total_travelers

        interests = context_dict.get("interests") or prefs.get("interests") or "sightseeing"
        food_info = prefs.get("food") if isinstance(prefs.get("food"), dict) else {}
        food_prefs = context_dict.get("dietary_preferences") or prefs.get("dietary_preferences") or food_info.get("preferences") or context_dict.get("food_preferences") or "Local delicacies"
        food_allergies = food_info.get("allergies") or ""

        accommodation = context_dict.get("accommodation_preference") or prefs.get("accommodation_preference") or "hotel"
        transportation = context_dict.get("transportation") or prefs.get("transportation") or "flight"
        pace = prefs.get("activity_pace") or context_dict.get("activity_pace") or "balanced"
        budget_type = context_dict.get("budget_tier") or prefs.get("budget_type") or prefs.get("preferred_budget") or "Mid-range"

        accessibility = prefs.get("accessibility") or ""
        ai_directives = prefs.get("ai") or ""
        daily_routine = prefs.get("daily_routine") if isinstance(prefs.get("daily_routine"), dict) else {}
        wake_time = daily_routine.get("wake_up_time", "08:00")
        sleep_time = daily_routine.get("sleep_time", "22:30")
        lunch_time = daily_routine.get("lunch_time", "13:00")
        dinner_time = daily_routine.get("dinner_time", "19:30")
        sunset_spot = daily_routine.get("preferred_viewpoint", "sunset")
        weather_pref = context_dict.get("preferred_climate") or prefs.get("preferred_climate") or prefs.get("weather") or "temperate"

        origin_city = context_dict.get("origin_city") or prefs.get("origin_city") or "Coimbatore"
        origin_airport = context_dict.get("origin_airport") or prefs.get("origin_airport") or ""
        dest_airport = context_dict.get("destination_airport") or prefs.get("destination_airport") or ""
        start_date = context_dict.get("start_date") or prefs.get("start_date") or ""
        end_date = context_dict.get("end_date") or prefs.get("end_date") or ""

        # 1. Companion & Group Travel Style Instructions (Derived purely from travel_style)
        style_instructions_list = []
        travel_style_clean = str(travel_style or "").lower().strip()

        if "solo" in travel_style_clean:
            style_instructions_list.append("""- SOLO TRAVELER PERSONALIZATION:
  * Select solo-friendly attractions, safe/public locations, and walkable exploration spots.
  * Recommend cafes, food markets, and casual dining comfortable for a single person.""")
        elif "friend" in travel_style_clean:
            style_instructions_list.append("""- FRIENDS GROUP PERSONALIZATION:
  * Prioritize group-friendly experiences, social dining, vibrant neighborhoods, and shared activities.""")
        elif "fam" in travel_style_clean:
            style_instructions_list.append("""- FAMILY TRAVEL PERSONALIZATION:
  * Prioritize family-friendly attractions with age-appropriate activities and comfortable pacing.""")
        elif "couple" in travel_style_clean or "romantic" in travel_style_clean:
            style_instructions_list.append("""- COUPLE / ROMANTIC PERSONALIZATION:
  * Include scenic viewpoints, romantic dining, relaxed evening strolls, and cultural highlights.""")
        elif "luxury" in travel_style_clean:
            style_instructions_list.append("""- LUXURY TRAVEL PERSONALIZATION:
  * Recommend high-end dining, premium cultural experiences, private/comfortable transit, and top-tier spots.""")
        elif "backpack" in travel_style_clean or "budget" in travel_style_clean:
            style_instructions_list.append("""- BACKPACKER / BUDGET PERSONALIZATION:
  * Focus on free/low-cost historic landmarks, local street food markets, walking trails, and public transit.""")

        # 2. Explicit User Interest Instructions (Derived purely from interests)
        interests_clean = str(interests or "").lower().strip()
        interest_instructions_list = []

        if "adventure" in interests_clean:
            interest_instructions_list.append("""- ADVENTURE INTEREST:
  * Prioritize outdoor exploration, scenic trails, nature treks, or active excursions.""")
        if "relax" in interests_clean or "peace" in interests_clean:
            interest_instructions_list.append("""- RELAXATION INTEREST:
  * Prioritize peaceful places, gardens, scenic viewpoints, spas, and unhurried schedules.""")
        if "cultur" in interests_clean or "heritage" in interests_clean or "history" in interests_clean:
            interest_instructions_list.append("""- CULTURAL & HISTORIC INTEREST:
  * Prioritize historic heritage, iconic monuments, architectural wonders, and museums.""")
        if "street food" in interests_clean or "local food" in interests_clean:
            interest_instructions_list.append("""- STREET FOOD & LOCAL DELICACIES:
  * Feature authentic local food stalls, markets, and regional street specialties.""")
        elif "luxury dining" in interests_clean:
            interest_instructions_list.append("""- FINE DINING & GASTRONOMY:
  * Feature celebrated culinary venues and acclaimed regional restaurants.""")
        if "nature" in interests_clean or "wildlife" in interests_clean or "hiking" in interests_clean:
            interest_instructions_list.append("""- NATURE & OUTDOOR INTEREST:
  * Prioritize national parks, botanical gardens, scenic natural viewpoints, and outdoor landscapes.""")
        if "shop" in interests_clean or "market" in interests_clean:
            interest_instructions_list.append("""- SHOPPING & MARKETS INTEREST:
  * Prioritize artisan markets, traditional craft bazaars, specialty boutiques, and shopping streets.""")
        if "photo" in interests_clean:
            interest_instructions_list.append("""- PHOTOGRAPHY INTEREST:
  * Prioritize scenic viewpoints, golden hour vantage points, and visually striking landmarks.""")
        if "hidden" in interests_clean or "gem" in interests_clean:
            interest_instructions_list.append("""- HIDDEN GEMS INTEREST:
  * Prioritize lesser-known, authentic local treasures away from dense tour groups.""")

        combined_personalization = style_instructions_list + interest_instructions_list
        style_instructions = "\n".join(combined_personalization)

        food_prefs_clean = str(food_prefs or "").strip().lower()
        has_specific_diet = any(k in food_prefs_clean for k in ["veg", "vegan", "halal", "kosher", "gluten", "dairy", "jain", "pescatarian"]) and not any(k in food_prefs_clean for k in ["no preference", "none", "unrestricted", "any"])
        if has_specific_diet:
            dietary_directive = f"""3. DIETARY REQUIREMENTS & DINING DIRECTIVE:
   * Traveler dietary requirement: '{food_prefs}'.
   * For ALL meal and dining activities, strictly recommend food spots and restaurants that cater to '{food_prefs}'.
   * Do NOT label a restaurant vegetarian, vegan, halal, kosher, or gluten-free unless reliable information supports that claim.
   * If dietary suitability of a recommended venue cannot be confirmed with certainty, include an explicit note in the description: 'Dietary suitability needs local confirmation.'
   * Recommend specific dishes matching '{food_prefs}'."""
        else:
            dietary_directive = f"""3. DIETARY REQUIREMENTS & DINING DIRECTIVE:
   * Traveler dietary requirement: '{food_prefs}' (Authentic Regional Cuisine / No Restrictions).
   * Feature authentic local restaurants, street food stalls, and regional specialties without imposing artificial dietary restrictions.
   * Do NOT assume or force vegetarian choices when 'No Preference' is selected."""

        # Stage A: Destination-Aware Candidate Retrieval (Independent of generation)
        discovered_candidates = fetch_real_pois_for_destination(destination, country)
        candidate_summary_lines = []
        if discovered_candidates:
            candidate_summary_lines.append(f"\n=========================\nSTAGE A: VERIFIED DESTINATION VENUES & CANDIDATES FOR {destination.upper()}\n=========================\nPrioritize selection and geographic grouping from these verified real places:")
            for c_poi in discovered_candidates[:25]:
                c_name = c_poi.get("name")
                c_cat = c_poi.get("category", "Sightseeing")
                c_is_dining = c_poi.get("is_dining", False)
                c_lat = c_poi.get("latitude")
                c_lon = c_poi.get("longitude")
                coord_str = f" (Lat: {c_lat}, Lon: {c_lon})" if c_lat and c_lon else ""
                dining_str = f" [Dining Venue - Signature: {c_poi.get('signature_dish') or c_poi.get('vegetarian_dish') or 'Local Regional Specialties'}]" if c_is_dining else ""
                candidate_summary_lines.append(f"- {c_name} | Category: {c_cat}{coord_str}{dining_str}")
        candidates_block = "\n".join(candidate_summary_lines)

        # Render prompt sections from v1 templates
        system_inst = PromptLoader.load("system", version=self.config.PROMPT_VERSION)
        
        curr_rules = PromptLoader.render("currency_rules", {
            "currency_code": curr_code,
            "currency_symbol": curr_symbol,
            "currency_country": curr_country,
            "budget": budget,
            "activities_budget": activities_alloc
        }, version=self.config.PROMPT_VERSION)

        act_rules = PromptLoader.render("activity_rules", {
            "total_days": total_days
        }, version=self.config.PROMPT_VERSION)

        schema_rules = PromptLoader.render("output_schema", {
            "destination": destination,
            "country": country,
            "total_days": total_days,
            "budget": budget,
            "currency_code": curr_code,
            "currency_symbol": curr_symbol,
            "current_iso_time": datetime.now(timezone.utc).isoformat()
        }, version=self.config.PROMPT_VERSION)

        prompt_str = f"""
=========================
COMPLETE TRAVELER PROFILE & TRIP DETAILS
=========================
Destination City/Region: {destination}
Country: {country}
Origin City: {origin_city} {f'(Airport: {origin_airport})' if origin_airport else ''}
Destination Airport: {dest_airport}
Travel Dates: {start_date} to {end_date}
Total Duration: EXACTLY {total_days} Days

TRAVELER COMPOSITION & STYLE:
- Travel Style: {travel_style} ({budget_type})
- Total Group Size: {group_size} ({adults} Adults, {children} Children, {seniors} Seniors, {pets} Pets)
- Primary Accommodation: {accommodation}
- Primary Transport Mode: {transportation}
- Daily Activity Pace: {pace}

BUDGET & ALLOCATION:
- Total Trip Budget: {budget} {curr_code}
- Estimated Daily Budget: {round(budget / max(total_days, 1), 2)} {curr_code}/day
- Estimated Activities Budget: {activities_alloc} {curr_code}

PERSONAL PREFERENCES & INTERESTS:
- Selected Activity Interests: {interests}
- Dining & Dietary Preferences: {food_prefs} {f'(Allergies: {food_allergies})' if food_allergies else ''}
- Accessibility Requirements: {accessibility if accessibility else 'None'}
- Weather & Climate Preference: {weather_pref}
- AI Directives / Preferences: {ai_directives if ai_directives else 'Standard high quality'}

DAILY ROUTINE SCHEDULING PREFERENCES:
- Target Wake Time: {wake_time} | Target Sleep Time: {sleep_time}
- Target Lunch Time: {lunch_time} | Target Dinner Time: {dinner_time}
- Preferred Viewpoint Slot: {sunset_spot}

=========================
PERSONALIZATION & SCHEDULING DIRECTIVES
=========================
1. DURATION: Generate EXACTLY {total_days} itinerary days (Day 1 to Day {total_days}).
2. PERSONALIZATION: Do NOT generate a generic itinerary. The selected activities, dining spots, transit mode, and daily schedule MUST directly reflect the selected interests ({interests}), travel style ({travel_style}), and traveler composition.
   * STRICT INTEREST PURITY RULE: Never inject or claim unselected interests (e.g. do NOT invent 'Solo' or 'Food & Dining' interests unless explicitly listed in Selected Activity Interests). Meals are basic logistics unless 'Street Food' or 'Luxury Dining' was selected.
{style_instructions}
{dietary_directive}
4. CLIMATE & WEATHER AWARENESS:
   * Traveler preferred climate: '{weather_pref}'.
   * Thoughtfully align outdoor and indoor activities to local weather realities and user climate preferences.
   * Do not make unverified claims about weather or climate.
5. BUDGET CONSTRAINTS & TIER INTERPRETATION:
   * Budget Tier: '{budget_type}' with estimated daily limit of {round(budget / max(total_days, 1), 2)} {curr_code}/day.
   * Keep accommodation, transport, meals, and activity costs within this tier.
   * Show a transparent cost estimate for each activity in {curr_code} ({curr_symbol}).
6. GEOGRAPHIC EFFICIENCY & PROXIMITY: Group daily activities in geographically close clusters to minimize travel time. Avoid unnecessary backtracking.
7. TRANSIT AUTHENTICITY: Do NOT assume a metro, railway, or airport exists where none does. Do NOT invent train routes or transport availability. Use real local transport (e.g. walking, e-rickshaws, cabs in Agra). Distinguish intercity transfers from local transit.
8. ARRIVAL & DEPARTURE LOGIC:
   * First Day (Day 1): Do NOT assume the user arrives early in the morning. If arrival time is unknown, avoid tightly scheduled activities. Schedule flexible, nearby afternoon exploration and state in the day's theme note: 'Schedule is flexible and depends on actual arrival time.'
   * Last Day (Day {total_days}): Do NOT schedule activities too close to departure. Keep schedule flexible. Allocate ample buffer for hotel checkout, souvenir shopping, and departure transfer. Never invent flight or train details.
9. HONEST DATA PROVENANCE:
   * Use strictly three statuses: 'Verified' (for confirmed real POIs), 'Estimated' (for approximate costs, durations, and suggested dining), and 'Unavailable' (for unconfirmed opening hours or accessibility).
   * Do NOT mark AI-generated prices as Verified.
   * Do NOT label dining activities or transit as 'Free Entry'.
10. INTEREST COMPATIBILITY:
   * If an interest has limited suitability at the destination (e.g. Gaming in historic {destination}), provide an explicit explanatory note (e.g. 'Gaming venues are limited in historic {destination}; prioritized local entertainment and vibrant bazaars') instead of fabricating fake places.

=========================
LANGUAGE REQUIREMENT & PROPER NOUNS
=========================
1. Generate ALL user-visible itinerary titles, descriptions, explanations, and theme notes strictly in {language}.
2. PRESERVE proper nouns: Official place names, airport names, transit stations, and provider identifiers must be preserved in their recognizable standard names.
3. Avoid unintended mixing of languages within sentences.

{candidates_block}

{curr_rules}

{act_rules}

{schema_rules}

{f"Regeneration ID: {context_dict.get('generation_id')} (Ensure this output is completely unique and different from previous versions)" if context_dict.get('generation_id') else ""}
"""

        # Stage A: Fast provider selection avoiding timeouts when keys are unconfigured
        import os
        env_def = os.getenv("AI_DEFAULT_PROVIDER", "").lower()
        if env_def == "mock":
            providers_to_try = ["mock"]
        else:
            has_gemini = bool(os.getenv("GEMINI_API_KEY"))
            has_groq = bool(os.getenv("GROQ_API_KEY"))

            providers_to_try = []
            if self.config.DEFAULT_PROVIDER == "gemini" and has_gemini:
                providers_to_try.append("gemini")
            elif self.config.DEFAULT_PROVIDER == "groq" and has_groq:
                providers_to_try.append("groq")
            elif self.config.DEFAULT_PROVIDER not in ["gemini", "groq"]:
                providers_to_try.append(self.config.DEFAULT_PROVIDER)

            if self.config.FALLBACK_PROVIDER == "groq" and has_groq and "groq" not in providers_to_try:
                providers_to_try.append("groq")
            elif self.config.FALLBACK_PROVIDER == "gemini" and has_gemini and "gemini" not in providers_to_try:
                providers_to_try.append("gemini")

            # Always include mock as final high-speed guarantee
            if "mock" not in providers_to_try:
                providers_to_try.append("mock")

        retry_count = 0
        fallback_used = False
        final_data = None
        used_provider_name = "mock"

        for p_idx, provider_name in enumerate(providers_to_try):
            # Enforce max execution budget per attempt to guarantee response in < 60s
            if (time.time() - start_time) > 25.0 and "mock" in providers_to_try:
                print(f"[Stage Instrumentation] Provider execution timeout budget exceeded. Switching directly to deterministic mock fallback.")
                break

            try:
                provider = AIProviderFactory.get_provider(provider_name)
                used_provider_name = provider_name
                
                # Execute generation
                raw_resp = provider.generate(prompt_str, system_instruction=system_inst)
                
                # Validate & Normalize
                ok, norm_data, err = ItineraryValidator.validate_and_normalize(raw_resp, currency_code=curr_code, requested_language=language)
                if ok and norm_data:
                    final_data = norm_data
                    if p_idx > 0:
                        fallback_used = True
                    break
                else:
                    print(f"[LANGUAGE VALIDATION] Retrying generation. Error: {err}")
                    if self.config.ENABLE_RETRY and retry_count < self.config.MAX_RETRIES and (time.time() - start_time) < 20.0:
                        retry_count += 1
                        raw_resp2 = provider.generate(prompt_str, system_instruction=system_inst)
                        ok2, norm_data2, err2 = ItineraryValidator.validate_and_normalize(raw_resp2, currency_code=curr_code, requested_language=language)
                        if ok2 and norm_data2:
                            final_data = norm_data2
                            break
            except Exception as e:
                print(f"[AI Provider Warning] Provider '{provider_name}' failed: {e}")
                fallback_used = True
                continue

        # If all LLMs fail or timed out, execute MockProvider deterministic fallback
        if not final_data:
            try:
                mock_p = AIProviderFactory.get_provider("mock")
                raw_mock = mock_p.generate(prompt_str, system_instruction=system_inst)
                _, final_data, _ = ItineraryValidator.validate_and_normalize(raw_mock, currency_code=curr_code, requested_language=language)
            except Exception as e:
                print(f"[AIEngine Mock Fallback Warning]: {e}")
                final_data = None
            fallback_used = True
            used_provider_name = "mock"

        existing_days = (final_data.get("trip") if isinstance(final_data, dict) else {}).get("days") or (final_data.get("trip") if isinstance(final_data, dict) else {}).get("itinerary_days")
        if not final_data or not existing_days:
            # Destination-independent fallback generator using ONLY authentic discovered candidates
            fallback_days = []
            from app.services.poi_service import is_valid_destination_poi
            from app.services.route_optimizer import destination_has_rail
            has_rail = destination_has_rail(destination)
            safe_trans = (transportation or "Walking")
            if not has_rail and any(k in safe_trans.lower() for k in ["train", "metro", "subway", "rail", "tram"]):
                safe_trans = "Taxi / Road Transport"

            valid_cands = [p for p in (discovered_candidates or []) if is_valid_destination_poi(p, destination)]
            
            # Separate dining and attractions
            c_dining = [p for p in valid_cands if p.get("is_dining") or p.get("category") in ["Restaurant", "Cafe", "Food Market", "Dining"]]
            c_attractions = [p for p in valid_cands if not p.get("is_dining") and p.get("category") not in ["Restaurant", "Cafe", "Food Market", "Dining"]]
            if not c_attractions:
                c_attractions = valid_cands

            used_names = set()
            for d in range(1, total_days + 1):
                d_acts = []
                # Pick 1 morning attraction
                avail_att = [p for p in c_attractions if p["name"].strip().lower() not in used_names]
                if avail_att:
                    p1 = avail_att[0]
                    used_names.add(p1["name"].strip().lower())
                    raw_ticket = p1.get("ticket_price")
                    t_amt = float(raw_ticket) if (raw_ticket is not None and float(raw_ticket) > 0) else 0.0
                    d_acts.append({
                        "id": f"act_safe_d{d}_01",
                        "start_time": "09:30",
                        "end_time": "12:00",
                        "duration_minutes": 150,
                        "time_slot": "morning",
                        "title": p1["name"],
                        "description": p1.get("description") or f"Explore {p1['name']} in {destination}.",
                        "place": {
                            "name": p1["name"],
                            "category": p1.get("category", "Sightseeing"),
                            "latitude": p1.get("latitude"),
                            "longitude": p1.get("longitude"),
                            "rating": p1.get("rating"),
                            "address": p1.get("address", destination)
                        },
                        "cost": {"amount": t_amt, "currency": curr_code, "symbol": curr_symbol, "estimated": True},
                        "ticket_price": t_amt,
                        "formatted_cost": f"{curr_symbol}{t_amt:,.0f}" if t_amt > 0 else ("Free Entry" if p1.get("is_free_verified") else "Price not verified"),
                        "transport_mode": safe_trans,
                        "ai_reason": p1.get("ai_reason") or f"✓ Verified landmark venue in {destination}",
                        "confidence_score": 0.98,
                        "provenance": p1.get("provenance") or {
                            "place_verification": f"Verified POI Database ({destination})",
                            "status": "Verified",
                            "overall_status": "Verified"
                        }
                    })

                # Pick 1 authentic dining venue if available
                avail_din = [p for p in c_dining if p["name"].strip().lower() not in used_names]
                if avail_din:
                    p_din = avail_din[0]
                    used_names.add(p_din["name"].strip().lower())
                    din_cost = float(p_din.get("meal_cost") or 25.0)
                    din_amt = round(CurrencyService.convert(din_cost, p_din.get("currency", "USD"), curr_code), 2) if p_din.get("currency", curr_code) != curr_code else din_cost
                    d_acts.append({
                        "id": f"act_safe_d{d}_02",
                        "start_time": "12:30",
                        "end_time": "14:00",
                        "duration_minutes": 90,
                        "time_slot": "lunch",
                        "title": p_din["name"],
                        "description": p_din.get("description") or f"Enjoy authentic dining at {p_din['name']}.",
                        "activity_type": "meal",
                        "is_dining": True,
                        "meal_type": "lunch",
                        "signature_dish": p_din.get("signature_dish"),
                        "dietary_suitability": p_din.get("dietary_suitability"),
                        "place": {
                            "name": p_din["name"],
                            "category": p_din.get("category", "Restaurant"),
                            "latitude": p_din.get("latitude"),
                            "longitude": p_din.get("longitude"),
                            "rating": p_din.get("rating"),
                            "address": p_din.get("address", destination)
                        },
                        "cost": {"amount": din_amt, "currency": curr_code, "symbol": curr_symbol, "estimated": True, "cost_type": "meal"},
                        "ticket_price": 0.0,
                        "meal_cost": din_amt,
                        "formatted_cost": f"Est. Meal: {curr_symbol}{din_amt:,.0f}",
                        "transport_mode": "Walking",
                        "ai_reason": p_din.get("ai_reason") or f"✓ Authentic regional culinary experience at {p_din['name']}",
                        "confidence_score": 0.95,
                        "provenance": p_din.get("provenance") or {
                            "place_verification": f"Verified Dining Venue ({destination})",
                            "status": "Verified",
                            "overall_status": "Verified"
                        }
                    })

                # Pick 1 afternoon attraction
                avail_att2 = [p for p in c_attractions if p["name"].strip().lower() not in used_names]
                if avail_att2:
                    p2 = avail_att2[0]
                    used_names.add(p2["name"].strip().lower())
                    raw_ticket2 = p2.get("ticket_price")
                    t_amt2 = float(raw_ticket2) if (raw_ticket2 is not None and float(raw_ticket2) > 0) else 0.0
                    d_acts.append({
                        "id": f"act_safe_d{d}_03",
                        "start_time": "14:30",
                        "end_time": "17:00",
                        "duration_minutes": 150,
                        "time_slot": "afternoon",
                        "title": p2["name"],
                        "description": p2.get("description") or f"Explore {p2['name']} in {destination}.",
                        "place": {
                            "name": p2["name"],
                            "category": p2.get("category", "Sightseeing"),
                            "latitude": p2.get("latitude"),
                            "longitude": p2.get("longitude"),
                            "rating": p2.get("rating"),
                            "address": p2.get("address", destination)
                        },
                        "cost": {"amount": t_amt2, "currency": curr_code, "symbol": curr_symbol, "estimated": True},
                        "ticket_price": t_amt2,
                        "formatted_cost": f"{curr_symbol}{t_amt2:,.0f}" if t_amt2 > 0 else ("Free Entry" if p2.get("is_free_verified") else "Price not verified"),
                        "transport_mode": safe_trans,
                        "ai_reason": p2.get("ai_reason") or f"✓ Verified landmark venue in {destination}",
                        "confidence_score": 0.98,
                        "provenance": p2.get("provenance") or {
                            "place_verification": f"Verified POI Database ({destination})",
                            "status": "Verified",
                            "overall_status": "Verified"
                        }
                    })

                # If all unique attractions are exhausted, schedule honest self-guided exploration/leisure
                if not d_acts:
                    d_acts.append({
                        "id": f"act_safe_d{d}_leisure",
                        "start_time": "10:00",
                        "end_time": "15:30",
                        "duration_minutes": 330,
                        "time_slot": "day",
                        "title": f"Independent Exploration & Leisure in {destination}",
                        "description": f"Dedicated leisure and personal discovery time in {destination}. Explore local neighborhood streets, artisan shops, or relax at your own pace without scheduled venue admissions.",
                        "activity_type": "area_suggestion",
                        "is_area_suggestion": True,
                        "place": {
                            "name": f"{destination} Leisure & Artisan District",
                            "category": "Area Suggestion",
                            "address": destination,
                            "latitude": None,
                            "longitude": None,
                            "rating": None
                        },
                        "cost": {"amount": 0.0, "currency": curr_code, "symbol": curr_symbol, "estimated": False},
                        "ticket_price": 0.0,
                        "formatted_cost": "Free Entry",
                        "transport_mode": "Walking",
                        "ai_reason": f"Honest leisure schedule: All verified curated destination landmarks in {destination} have been experienced on prior days.",
                        "confidence_score": 0.90,
                        "provenance": {
                            "place_verification": "Area Exploration",
                            "status": "Unavailable",
                            "overall_status": "Unavailable",
                            "identity_status": "Estimated",
                            "location_status": "Estimated",
                            "coordinate_status": "Unavailable",
                            "hours_status": "Tentative schedule",
                            "price_status": "Free Public Access",
                            "route_status": "Route unavailable",
                            "rating_status": "Unrated",
                            "last_verified": "2026-11-10T00:00:00Z"
                        }
                    })

                fallback_days.append({
                    "day_number": d,
                    "title": f"Day {d}: {destination} Highlights",
                    "theme_note": f"Exploration in {destination}" + (f": {d_acts[0]['title']}" if d_acts else ""),
                    "activities": d_acts
                })
            final_data = {"trip": {"destination": destination, "days": fallback_days, "total_days": total_days}}

        elapsed_ms = int((time.time() - start_time) * 1000)

        trip_dict = final_data.get("trip") if isinstance(final_data, dict) and "trip" in final_data else (final_data or {})
        if "days" in trip_dict and "itinerary_days" not in trip_dict:
            trip_dict["itinerary_days"] = trip_dict["days"]
        elif "itinerary_days" in trip_dict and "days" not in trip_dict:
            trip_dict["days"] = trip_dict["itinerary_days"]

        # Build Versioned Response Envelope
        envelope = AIResponse(
            schema_version="1.0",
            metadata=AIResponseMetadata(
                provider=used_provider_name.capitalize(),
                model="gemini-2.5-flash" if used_provider_name == "gemini" else ("llama-3.3-70b" if used_provider_name == "groq" else "mock-travel-planner"),
                generation_time_ms=elapsed_ms,
                retry_count=retry_count,
                fallback_used=fallback_used,
                generated_at=datetime.now(timezone.utc).isoformat()
            ),
            trip=trip_dict
        )


        return envelope.model_dump()
