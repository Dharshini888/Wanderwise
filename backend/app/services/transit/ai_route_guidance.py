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
        provider_failures: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates structured, high-level unverified travel steps for route_guidance.
        Used as Level 3 fallback when verified transit and alternatives are unavailable.
        """
        scale = (journey_scale or "DOMESTIC").upper()

        if scale == "INTERCONTINENTAL":
            steps = [
                {
                    "sequence": 1,
                    "mode": "LOCAL_TRANSFER",
                    "description": f"Travel from {origin_name} area to a major international airport using local taxi or ground transfer."
                },
                {
                    "sequence": 2,
                    "mode": "FLIGHT",
                    "description": f"Take a commercial international flight from {origin_country or 'origin region'} to {dest_country or 'destination region'}."
                },
                {
                    "sequence": 3,
                    "mode": "LOCAL_TRANSIT",
                    "description": f"From the arrival airport, use verified local rail, airport express, metro, or taxi services to reach central {dest_name}."
                }
            ]
            recommended_mode = "Air Travel"
        elif scale == "INTERNATIONAL":
            steps = [
                {
                    "sequence": 1,
                    "mode": "LOCAL_TRANSFER",
                    "description": f"Travel from {origin_name} to the nearest international transit hub or airport."
                },
                {
                    "sequence": 2,
                    "mode": "INTERNATIONAL_TRAVEL",
                    "description": f"Use cross-border high-speed rail, intercity bus, or commercial flight toward {dest_name}."
                },
                {
                    "sequence": 3,
                    "mode": "LOCAL_TRANSIT",
                    "description": f"Use local urban transit (metro/bus) to reach your final destination in {dest_name}."
                }
            ]
            recommended_mode = "International Rail / Air Travel"
        else: # DOMESTIC or SAME_CITY
            steps = [
                {
                    "sequence": 1,
                    "mode": "LOCAL_ACCESS",
                    "description": f"Travel from {origin_name} to the main intercity railway station or bus terminal."
                },
                {
                    "sequence": 2,
                    "mode": "INTERCITY_TRAVEL",
                    "description": f"Use regional/intercity passenger rail or highway coach toward {dest_name}."
                },
                {
                    "sequence": 3,
                    "mode": "LOCAL_ARRIVALS",
                    "description": f"From the arrival hub, use local city bus, auto, metro, or taxi to reach {dest_name}."
                }
            ]
            recommended_mode = "Intercity Rail / Coach"

        guidance_payload = {
            "verified": False,
            "type": "AI_GUIDANCE",
            "warning": "This is a suggested travel structure, not a verified itinerary. Schedules, platforms, and fares could not be verified from live providers.",
            "journey_scale": scale,
            "recommended_mode": recommended_mode,
            "steps": steps,
            "explanation": f"Public transit schedule could not be verified from live GTFS providers for {origin_name} → {dest_name}. WanderWise did not generate exact timetables or service numbers.",
        }

        # Zero-fabrication contract validation
        if not validate_no_ai_transit_facts(guidance_payload):
            logger.error("[AI GUIDANCE] Zero-fabrication contract check failed! Discarding AI guidance payload.")
            return {
                "verified": False,
                "type": "AI_GUIDANCE_REJECTED",
                "warning": "Route guidance was rejected due to zero-fabrication safety rules.",
                "steps": [],
            }

        logger.info(f"[AI GUIDANCE] High-level route guidance generated for {origin_name} -> {dest_name} ({scale})")
        return guidance_payload
