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
        distance_km: float = 0.0,
        road_distance_km: Optional[float] = None,
        rail_distance_km: Optional[float] = None,
        search_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates structured AI mode guidance for route fallbacks.
        Used as Level 3 fallback when verified transit and alternatives are unavailable.
        Strictly deterministic geographic classification and zero-fabrication.
        """
        scale = (journey_scale or "DOMESTIC").upper()
        straight_line_dist = round(float(distance_km or 0.0), 1)

        # Country context string
        if origin_country and dest_country and origin_country != "UNKNOWN" and dest_country != "UNKNOWN":
            if scale in ("DOMESTIC", "SAME_CITY"):
                country_context = f"within {origin_country}"
            else:
                country_context = f"from {origin_country} to {dest_country}"
        else:
            country_context = f"{scale.lower()} journey"

        if scale in ["INTERCONTINENTAL", "INTERNATIONAL"] or straight_line_dist > 1000:
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is {scale.lower()} ({country_context}) "
                f"with a straight-line distance of approximately {straight_line_dist} km. "
                f"Flight is recommended as the practical primary mode. However, no flight itinerary was verified by connected providers."
            )
        elif straight_line_dist > 500:
            rec_mode = "Rail / Flight"
            title = "Rail or Flight Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is {scale.lower()} ({country_context}) "
                f"with a straight-line distance of approximately {straight_line_dist} km. "
                f"Rail or domestic flight is the practical primary mode, but no verified itinerary was returned."
            )
        else:
            rec_mode = "Driving / Coach"
            title = "Driving or Coach Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is a {scale.lower()} route ({country_context}) "
                f"with a straight-line distance of approximately {straight_line_dist} km. "
                f"Driving, intercity coach, or regional rail are practical modes, but no verified public transit itinerary was returned."
            )

        prov_status = {
            "railradar": "no_verified_itinerary",
            "flight_provider": "no_verified_itinerary"
        }
        limitations = [
            "No verified FlightProvider itinerary was available",
            "No verified RailRadar itinerary was available",
            "No public transit schedule was confirmed by connected transit providers"
        ]

        guidance_payload = {
            "type": "AI_MODE_GUIDANCE",
            "search_id": search_id,
            "origin": origin_name,
            "destination": dest_name,
            "scale": scale,
            "recommended_mode": rec_mode,
            "verification": "estimated",
            "title": title,
            "reason": reason,
            "distances": {
                "straight_line_distance_km": straight_line_dist,
                "road_distance_km": round(float(road_distance_km), 1) if road_distance_km else None,
                "rail_distance_km": round(float(rail_distance_km), 1) if rail_distance_km else None,
            },
            "provider_status": prov_status,
            "limitations": limitations,
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
