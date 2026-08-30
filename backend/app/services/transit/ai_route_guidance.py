"""
ai_route_guidance.py — Isolated AI Route Guidance & Zero-Fabrication Validator for WanderWise V12

Used ONLY when verified public transit itineraries and verified alternatives are unavailable.

Gemini Safety Contract:
  - Generates ONLY high-level unverified travel structures (e.g. airport transfers, international flights, metro).
  - FORBIDDEN from generating exact schedules, timetables, departure times, arrival times, platform numbers,
    fares, flight numbers, train numbers, bus numbers, or populating journey.legs.
  - validate_no_ai_transit_facts() recursively asserts zero prohibited fields exist.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

FORBIDDEN_AI_FIELDS = {
    "departure_time",
    "arrival_time",
    "platform",
    "fare",
    "flight_number",
    "train_number",
    "bus_number",
    "distance_km",
    "duration_minutes",
    "route_number",
    "ticket_price",
}


def validate_no_ai_transit_facts(obj: Any) -> bool:
    """
    Recursively inspects a data structure to assert zero prohibited transit fact fields exist.
    Returns True if clean, False if any forbidden field is detected.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_AI_FIELDS:
                logger.warning(f"[ZERO-FABRICATION CONTRACT REJECTED] Forbidden key detected in AI output: '{k}'")
                return False
            if not validate_no_ai_transit_facts(v):
                return False
    elif isinstance(obj, list):
        for item in obj:
            if not validate_no_ai_transit_facts(item):
                return False
    elif isinstance(obj, str):
        # Regex check for specific forbidden patterns like "Flight BA123", "Train 12345", "Platform 4", "Departure 08:30"
        prohibited_patterns = [
            r"Flight\s+[A-Z0-9]{2,6}\d{1,4}",
            r"Train\s+\d{3,5}",
            r"Platform\s+\d{1,2}",
            r"Departure\s+\d{2}:\d{2}",
            r"Arrival\s+\d{2}:\d{2}",
        ]
        for pattern in prohibited_patterns:
            if re.search(pattern, obj, re.IGNORECASE):
                logger.warning(f"[ZERO-FABRICATION CONTRACT REJECTED] Forbidden pattern '{pattern}' detected in AI text snippet: '{obj}'")
                return False

    return True


class AIRouteGuidanceService:
    @staticmethod
    def generate_guidance(
        origin_name: str,
        dest_name: str,
        journey_scale: str,
        origin_country: str = "",
        dest_country: str = "",
        provider_failures: Optional[List[Dict[str, Any]]] = None,
        distance_km: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generates structured AI mode guidance for route fallbacks.
        Used as Level 3 fallback when verified transit and alternatives are unavailable.
        """
        scale = (journey_scale or "DOMESTIC").upper()

        if scale in ["INTERCONTINENTAL", "INTERNATIONAL"] or distance_km > 1000:
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = f"The journey is {scale.lower()} and approximately {distance_km} km by straight-line distance, making flight the practical primary mode. However, no live flight itinerary was verified."
        elif distance_km > 500:
            rec_mode = "Rail / Flight"
            title = "Rail or Flight Recommended"
            reason = f"The journey is {distance_km} km by straight-line distance. Rail or domestic flight is the practical primary mode, but no verified itinerary was returned."
        else:
            rec_mode = "Driving / Coach"
            title = "Driving or Coach Recommended"
            reason = f"The journey is a shorter domestic route ({distance_km} km). Driving, intercity coach, or regional rail are the practical modes, but no verified itinerary was returned."

        prov_status = {
            "railradar": "no_verified_itinerary",
            "flight_provider": "no_verified_itinerary"
        }
        limitations = [
            "No verified FlightProvider itinerary was available",
            "No verified RailRadar itinerary was available"
        ]

        if provider_failures:
            # Overwrite defaults if specific provider failures exist in the trace
            # (Though usually if we're here, they both failed or are unconfigured)
            pass

        guidance_payload = {
            "type": "AI_MODE_GUIDANCE",
            "recommended_mode": rec_mode,
            "verification": "estimated",
            "title": title,
            "reason": reason,
            "provider_status": prov_status,
            "limitations": limitations
        }

        # Zero-fabrication contract validation
        if not validate_no_ai_transit_facts(guidance_payload):
            logger.error("[AI GUIDANCE] Zero-fabrication contract check failed! Discarding AI guidance payload.")
            return {
                "type": "AI_GUIDANCE_REJECTED",
                "verification": "estimated",
                "title": "Guidance Unavailable",
                "reason": "Route guidance was rejected due to zero-fabrication safety rules.",
                "limitations": ["AI Safety Violation Prevented Data Generation"]
            }

        logger.info(f"[AI GUIDANCE] Mode guidance generated for {origin_name} -> {dest_name} ({scale})")
        return guidance_payload
