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
        activities_budget = context_dict.get("activities_budget", round(budget * 0.15, 2))

        # Render prompt sections from v1 templates
        system_inst = PromptLoader.load("system", version=self.config.PROMPT_VERSION)
        
        curr_rules = PromptLoader.render("currency_rules", {
            "currency_code": curr_code,
            "currency_symbol": curr_symbol,
            "currency_country": curr_country,
            "budget": budget,
            "activities_budget": activities_budget
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
TRIP DETAILS
=========================
Destination: {destination}
Country: {country}
Total Days: {total_days}
Budget: {budget} {curr_code}
Travel Style: {context_dict.get("travel_style", "solo")}

{curr_rules}

{act_rules}

{schema_rules}
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
                ok, norm_data, err = ItineraryValidator.validate_and_normalize(raw_resp, currency_code=curr_code)
                if ok and norm_data:
                    final_data = norm_data
                    if p_idx > 0:
                        fallback_used = True
                    break
                else:
                    # Retry once if enabled
                    if self.config.ENABLE_RETRY and retry_count < self.config.MAX_RETRIES:
                        retry_count += 1
                        raw_resp2 = provider.generate(prompt_str, system_instruction=system_inst)
                        ok2, norm_data2, err2 = ItineraryValidator.validate_and_normalize(raw_resp2, currency_code=curr_code)
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
            _, final_data, _ = ItineraryValidator.validate_and_normalize(raw_mock, currency_code=curr_code)
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
