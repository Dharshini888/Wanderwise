import time
from datetime import datetime
from typing import Dict, Any, Optional
from app.config.ai_config import ai_settings
from app.ai.providers.provider_factory import AIProviderFactory
from app.ai.prompt_loader import PromptLoader
from app.ai.validators.itinerary_validator import ItineraryValidator
from app.schemas.ai_response import AIResponse, AIResponseMetadata

class AIEngine:
    """Central AI Engine Orchestrator managing context building, prompt rendering, provider execution, retries, 5-stage validation, and response envelope generation."""

    def __init__(self):
        self.config = ai_settings

    def generate_trip(self, context_dict: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        destination = context_dict.get("destination", "Destination")
        country = context_dict.get("country") or destination
        total_days = context_dict.get("total_days", 2)
        budget = context_dict.get("budget", 1000.0)
        curr_code = context_dict.get("currency_code", "USD")
        curr_symbol = context_dict.get("currency_symbol", "$")
        curr_country = context_dict.get("currency_country", country)
        activities_alloc = context_dict.get("activities_budget", round(budget * 0.15, 2))
        language = context_dict.get("language", "English")

        # Extract rich wizard details
        prefs = context_dict.get("trip_preferences") or {}
        travel_style = context_dict.get("travel_style") or prefs.get("travel_style") or "solo"
        group_size = context_dict.get("group_size") or 1
        travelers_dict = prefs.get("travelers") if isinstance(prefs.get("travelers"), dict) else {}
        adults = travelers_dict.get("adults") or 1
        children = travelers_dict.get("children") or 0
        seniors = travelers_dict.get("seniors") or 0
        pets = travelers_dict.get("pets") or 0

        interests = context_dict.get("interests") or prefs.get("interests") or "sightseeing"
        food_info = prefs.get("food") if isinstance(prefs.get("food"), dict) else {}
        food_prefs = food_info.get("preferences") or context_dict.get("food_preferences") or "Local delicacies"
        food_allergies = food_info.get("allergies") or ""

        accommodation = context_dict.get("accommodation_preference") or prefs.get("accommodation_preference") or "hotel"
        transportation = context_dict.get("transportation") or prefs.get("transportation") or "flight"
        pace = prefs.get("activity_pace") or context_dict.get("activity_pace") or "balanced"
        budget_type = prefs.get("budget_type") or "Mid-range"

        accessibility = prefs.get("accessibility") or ""
        ai_directives = prefs.get("ai") or ""
        daily_routine = prefs.get("daily_routine") if isinstance(prefs.get("daily_routine"), dict) else {}
        wake_time = daily_routine.get("wake_up_time", "08:00")
        sleep_time = daily_routine.get("sleep_time", "22:30")
        lunch_time = daily_routine.get("lunch_time", "13:00")
        dinner_time = daily_routine.get("dinner_time", "19:30")
        sunset_spot = daily_routine.get("preferred_viewpoint", "sunset")
        weather_pref = prefs.get("weather") or "mix"

        origin_city = context_dict.get("origin_city") or prefs.get("origin_city") or "Coimbatore"
        origin_airport = context_dict.get("origin_airport") or prefs.get("origin_airport") or ""
        dest_airport = context_dict.get("destination_airport") or prefs.get("destination_airport") or ""
        start_date = context_dict.get("start_date") or prefs.get("start_date") or ""
        end_date = context_dict.get("end_date") or prefs.get("end_date") or ""

        # Personalized Companion Instructions
        style_instructions = ""
        style_lower = str(travel_style).lower()
        if "solo" in style_lower:
            style_instructions = """
- SOLO TRAVELER PERSONALIZATION:
  * Select solo-friendly attractions, safe/public locations, and walkable exploration spots.
  * Recommend cafes, food markets, and casual dining comfortable for a single person.
  * Avoid forcing group-only activities or expensive group tours unless marked optional.
  * Include practical safety considerations and local tips for solo exploration.
"""
        elif "friend" in style_lower:
            style_instructions = """
- FRIENDS GROUP PERSONALIZATION:
  * Prioritize group-friendly experiences, social dining, vibrant neighborhoods, and shared activities.
  * Include lively food streets, photo spots, adventure/entertainment, and group transportation options.
  * Balance social activities with reasonable group pacing.
"""
        elif "fam" in style_lower:
            style_instructions = """
- FAMILY TRAVEL PERSONALIZATION:
  * Prioritize family-friendly attractions with age-appropriate activities.
  * Provide shorter travel segments, rest periods, and comfortable dining options suitable for children/seniors.
  * Avoid adult-only nightlife; keep pacing relaxed and manageable.
"""
        elif "couple" in style_lower or "romantic" in style_lower:
            style_instructions = """
- COUPLE / ROMANTIC PERSONALIZATION:
  * Include scenic viewpoints, romantic dining, relaxed evening strolls, and cultural highlights.
  * Pacing should be intimate and unhurried.
"""
        elif "luxury" in style_lower:
            style_instructions = """
- LUXURY TRAVEL PERSONALIZATION:
  * Recommend high-end dining, premium cultural experiences, private/comfortable transit, and top-tier spots.
"""
        elif "backpack" in style_lower or "budget" in style_lower:
            style_instructions = """
- BACKPACKER / BUDGET PERSONALIZATION:
  * Focus on free/low-cost historic landmarks, local street food markets, walking trails, and public transit.
"""

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
            "current_iso_time": datetime.utcnow().isoformat()
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
{style_instructions}
3. INTERESTS IN ACTION: If interests include History, include historic landmarks/museums; if Street Food, include real street food markets; if Photography, include scenic viewpoints/sunset spots; if Local Culture, include heritage districts.
4. GEOGRAPHIC EFFICIENCY & PROXIMITY: Group daily activities in geographically close clusters to minimize travel time.
5. OPERATING HOURS & MEAL TIME WINDOWS: Respect opening hours. Schedule lunch around {lunch_time} and dinner around {dinner_time}.
6. ACCURACY: Do NOT invent real-time live flight numbers or unverified live ticket prices. Mark unverified pricing as estimated.

=========================
LANGUAGE REQUIREMENT
=========================
Generate ALL user-visible itinerary content strictly in {language}.

{curr_rules}

{act_rules}

{schema_rules}

{f"Regeneration ID: {context_dict.get('generation_id')} (Ensure this output is completely unique and different from previous versions)" if context_dict.get('generation_id') else ""}
"""

        # 5-Stage Retry & Execution Pipeline
        providers_to_try = [self.config.DEFAULT_PROVIDER, self.config.FALLBACK_PROVIDER, "mock"]
        retry_count = 0
        fallback_used = False
        final_data = None
        used_provider_name = "mock"

        for p_idx, provider_name in enumerate(providers_to_try):
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
                    # Retry once if enabled
                    if self.config.ENABLE_RETRY and retry_count < self.config.MAX_RETRIES:
                        retry_count += 1
                        raw_resp2 = provider.generate(prompt_str, system_instruction=system_inst)
                        ok2, norm_data2, err2 = ItineraryValidator.validate_and_normalize(raw_resp2, currency_code=curr_code, requested_language=language)
                        if ok2 and norm_data2:
                            final_data = norm_data2
                            break
            except Exception:
                fallback_used = True
                continue

        # If all LLMs fail, execute MockProvider deterministic fallback
        if not final_data:
            mock_p = AIProviderFactory.get_provider("mock")
            raw_mock = mock_p.generate(prompt_str, system_instruction=system_inst)
            _, final_data, _ = ItineraryValidator.validate_and_normalize(raw_mock, currency_code=curr_code, requested_language=language)
            fallback_used = True
            used_provider_name = "mock"

        elapsed_ms = int((time.time() - start_time) * 1000)

        trip_dict = final_data.get("trip") if isinstance(final_data, dict) and "trip" in final_data else (final_data or {})

        # Build Versioned Response Envelope
        envelope = AIResponse(
            schema_version="1.0",
            metadata=AIResponseMetadata(
                provider=used_provider_name.capitalize(),
                model="gemini-2.5-flash" if used_provider_name == "gemini" else ("llama-3.3-70b" if used_provider_name == "groq" else "mock-travel-planner"),
                generation_time_ms=elapsed_ms,
                retry_count=retry_count,
                fallback_used=fallback_used,
                generated_at=datetime.utcnow().isoformat()
            ),
            trip=trip_dict
        )


        return envelope.model_dump()
