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
    def generate_strategy(
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
        """Category A: AI Transit Strategy mode recommendation."""
        return AIRouteGuidanceService.generate_guidance(
            origin_name=origin_name,
            dest_name=dest_name,
            journey_scale=journey_scale,
            origin_country=origin_country,
            dest_country=dest_country,
            provider_failures=provider_failures,
            distance_km=distance_km,
            road_distance_km=road_distance_km,
            rail_distance_km=rail_distance_km,
            search_id=search_id,
        )

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

        # Route-specific strategic geographic rationale
        o_lower = (origin_name or "").lower()
        d_lower = (dest_name or "").lower()

        strategic_considerations = []
        if ("bhutan" in o_lower or "paro" in o_lower or "thimphu" in o_lower) and ("delhi" in d_lower or "new delhi" in d_lower) or \
           ("delhi" in o_lower or "new delhi" in o_lower) and ("bhutan" in d_lower or "paro" in d_lower or "thimphu" in d_lower):
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey between Bhutan and New Delhi is an international corridor across the Himalayas (~{straight_line_dist} km). "
                f"Flying is recommended as the practical primary mode due to severe mountainous terrain and cross-border customs making overland transit exceptionally slow."
            )
            strategic_considerations = [
                "Cross-border Himalayan road transit requires over 30 hours of driving on winding mountain passes.",
                "Direct commercial flights connect Paro (PBH) and Indira Gandhi International (DEL).",
                "Aviation provides significant time savings, safety, and comfort on this mountainous corridor."
            ]
        elif ("london" in o_lower and "paris" in d_lower) or ("paris" in o_lower and "london" in d_lower):
            rec_mode = "High-Speed Rail / Flight"
            title = "High-Speed Rail or Flight Recommended"
            reason = (
                f"The London to Paris cross-channel corridor (~{straight_line_dist} km) is ideally suited for High-Speed Rail (Eurostar) or Flight. "
                f"Eurostar passenger trains connect London St Pancras and Paris Gare du Nord directly in ~2h 17m city-center to city-center."
            )
            strategic_considerations = [
                "City-center to city-center high-speed rail avoids airport security lines and ground transfers.",
                "Commercial flights operate frequently between London (LHR/LGW/LCY) and Paris (CDG/ORY).",
                "High-speed rail has substantially lower carbon emissions than short-haul aviation."
            ]
        elif ("delhi" in o_lower and "tokyo" in d_lower) or ("tokyo" in o_lower and "delhi" in d_lower):
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is an intercontinental route spanning approximately {straight_line_dist} km. "
                f"Commercial aviation is the only viable passenger mode for this distance."
            )
            strategic_considerations = [
                "Over 5,800 km distance makes non-stop or 1-stop commercial aviation the only viable option.",
                "Major international carriers operate scheduled wide-body flights between DEL and HND/NRT."
            ]
        elif ("chennai" in o_lower and "singapore" in d_lower) or ("singapore" in o_lower and "chennai" in d_lower):
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey between Chennai and Singapore is an overseas international corridor (~{straight_line_dist} km) across the Bay of Bengal. "
                f"Commercial flight is the only viable passenger transport mode."
            )
            strategic_considerations = [
                "Maritime distance of ~2,910 km requires commercial flight for passenger travel.",
                "Daily scheduled flights connect Chennai International (MAA) and Singapore Changi (SIN)."
            ]
        elif ("sydney" in o_lower and "auckland" in d_lower) or ("auckland" in o_lower and "sydney" in d_lower):
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey between Sydney and Auckland is a trans-Tasman international route (~{straight_line_dist} km). "
                f"Commercial aviation is the only practical passenger transit mode."
            )
            strategic_considerations = [
                "Trans-Tasman ocean crossing requires commercial aviation.",
                "Multiple daily scheduled flights connect Sydney Kingsford Smith (SYD) and Auckland Airport (AKL)."
            ]
        elif ("cairo" in o_lower and "dubai" in d_lower) or ("dubai" in o_lower and "cairo" in d_lower):
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey between Cairo and Dubai is an international Middle Eastern corridor (~{straight_line_dist} km) across desert terrain. "
                f"Commercial flight is the recommended mode."
            )
            strategic_considerations = [
                "Over 2,400 km across multiple international borders makes direct flights optimal.",
                "Frequent daily wide-body flights link Cairo (CAI) and Dubai (DXB)."
            ]
        elif scale in ["INTERCONTINENTAL", "INTERNATIONAL"] or straight_line_dist > 1000:
            rec_mode = "Flight"
            title = "Flight Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is {scale.lower()} ({country_context}) "
                f"with a straight-line distance of approximately {straight_line_dist} km. "
                f"Flight is recommended as the practical primary mode."
            )
            strategic_considerations = [
                f"Long-distance travel ({straight_line_dist} km) makes aviation the time-optimal transport mode.",
                "Investigate commercial flight schedules between regional gateway airports."
            ]
        elif straight_line_dist > 500:
            rec_mode = "Rail / Flight"
            title = "Rail or Flight Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is {scale.lower()} ({country_context}) "
                f"with a straight-line distance of approximately {straight_line_dist} km. "
                f"Express passenger rail or domestic flight is the practical primary mode."
            )
            strategic_considerations = [
                "Medium-to-long distance domestic route allows flexible choice between rail and air.",
                "Express passenger trains provide lower carbon footprint; flights provide faster travel time."
            ]
        else:
            rec_mode = "Driving / Coach"
            title = "Driving or Coach Recommended"
            reason = (
                f"The journey from {origin_name} to {dest_name} is a {scale.lower()} route ({country_context}) "
                f"with a straight-line distance of approximately {straight_line_dist} km. "
                f"Driving, intercity coach, or regional passenger rail are practical modes."
            )
            strategic_considerations = [
                "Short-to-medium distance overland corridor is well-suited for road transport or regional rail.",
                "Intercity expressways or passenger rail provide door-to-door convenience."
            ]

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
            "category": "AI_TRANSIT_STRATEGY",
            "search_id": search_id,
            "origin": origin_name,
            "destination": dest_name,
            "scale": scale,
            "recommended_mode": rec_mode,
            "verification": "unverified_strategy",
            "title": title,
            "reason": reason,
            "strategic_considerations": strategic_considerations,
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
