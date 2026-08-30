"""
transit_router.py — WanderWise Transit V13.0 Provider Priority Router
Now with RouteOptimizer and multi-route collection.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from .journey_classifier import JourneyClassifier
from .ai_route_guidance import AIRouteGuidanceService
from .itinerary_validator import validate_itinerary
from .providers.base import ProviderStatus, ProviderResult
from .providers.transitous_provider import TransitousProvider
from .providers.railradar_provider import RailRadarProvider
from .providers.gtfs_provider import GTFSLocalProvider
from .providers.osrm_provider import OSRMRoadProvider
from .providers.flight_provider import FlightProvider
from ..location.location_normalizer import check_location_sanity
from .route_optimizer import RouteOptimizer
from .journey_stitcher import stitch_all_journeys

logger = logging.getLogger(__name__)

MAX_DOMESTIC_ROAD_DISTANCE_KM = 800.0

def validate_flight_result(result: ProviderResult) -> Dict[str, Any]:
    if not result or result.status != ProviderStatus.SUCCESS or not result.itineraries:
        return {"valid": False, "reason": "Flight provider returned no verified flight itinerary"}

    valid_itineraries = []
    for itin in result.itineraries:
        orig = itin.get("origin_airport")
        dest = itin.get("destination_airport")

        if not orig or not dest or orig in ["UNKNOWN", "Origin Airport"] or dest in ["UNKNOWN", "Destination Airport"]:
            continue

        flight_num = itin.get("flight_number")
        dep = itin.get("departure_time")
        arr = itin.get("arrival_time")
        dur = itin.get("duration_minutes")

        if flight_num and flight_num not in ["Flight Option", "UNKNOWN"] and (dep or arr or (dur is not None and dur > 0)):
            clean_itin = dict(itin)
            if clean_itin.get("distance_km") == 0:
                clean_itin["distance_km"] = None
            if clean_itin.get("duration_minutes") == 0:
                clean_itin["duration_minutes"] = None
            valid_itineraries.append(clean_itin)

    if valid_itineraries:
        return {"valid": True, "itineraries": valid_itineraries}

    return {"valid": False, "reason": "Flight provider response contained incomplete airport/schedule data"}


class TransitRouter:
    def __init__(self):
        self.transit_providers = [
            RailRadarProvider(),
            TransitousProvider(),
            GTFSLocalProvider(),
        ]
        self.flight_provider = FlightProvider()

    def route(
        self,
        origin_name: str,
        origin_lat: float,
        origin_lon: float,
        dest_name: str,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes V13.0 Multimodal Router pipeline with full route optimization.
        """
        provider_trace: List[Dict[str, Any]] = []
        provider_audit: Dict[str, Dict[str, Any]] = {}
        why_this_route: List[str] = []
        
        all_routes = []

        orig_dict = {"name": origin_name, "lat": origin_lat, "lon": origin_lon}
        dest_dict = {"name": dest_name, "lat": dest_lat, "lon": dest_lon}
        sanity = check_location_sanity(orig_dict, dest_dict)

        if sanity.get("same_location"):
            logger.info(f"[ROUTER V13.0] SAME_LOCATION triggered ({origin_name} -> {dest_name})")
            why_this_route.append(f"Origin '{origin_name}' and destination '{dest_name}' are within 500 meters.")
            return {
                "status": "SAME_LOCATION",
                "result_level": 0,
                "journey_scale": "SAME_LOCATION",
                "origin": origin_name,
                "destination": dest_name,
                "routes": [],
                "route_guidance": None,
                "provider_trace": provider_trace,
                "provider_audit": provider_audit,
                "why_this_route": why_this_route,
                "message": "Origin and destination are practically identical.",
            }

        classification = JourneyClassifier.classify(
            origin_lat, origin_lon, dest_lat, dest_lon, origin_name, dest_name
        )
        scale = classification.get("scale", "DOMESTIC")
        dist_km = classification.get("distance_km", 0)

        # ── LEVEL 1: Evaluate Public Transit & Rail Providers ───────────
        provider_prefs = dict(preferences or {})
        provider_prefs["origin_name"] = origin_name
        provider_prefs["dest_name"] = dest_name

        for provider in self.transit_providers:
            logger.info(f"[ROUTER V13.0] Evaluating provider: {provider.provider_name}")
            try:
                result = provider.plan_journey(
                    origin_lat, origin_lon, dest_lat, dest_lon, departure_time, provider_prefs
                )
            except Exception as e:
                logger.warning(f"[ROUTER V13.0] Provider {provider.provider_name} raised exception: {e}")
                result = ProviderResult(
                    status=ProviderStatus.PROVIDER_UNAVAILABLE,
                    provider_name=provider.provider_name,
                    error=str(e)[:150],
                )

            p_status = result.status.value if (result and result.status) else "PROVIDER_UNAVAILABLE"
            provider_trace.append({"provider": provider.provider_name, "status": p_status, "note": result.note})
            provider_audit[provider.provider_name] = {
                "configured": p_status != "PROVIDER_NOT_CONFIGURED",
                "attempted": True,
                "status": p_status,
                "reason": result.note or result.error,
            }

            if result and result.status == ProviderStatus.SUCCESS and result.itineraries:
                for itin in result.itineraries:
                    v_report = validate_itinerary(itin)
                    if v_report.get("valid"):
                        raw_legs = itin.get("legs", [])
                        mode = (raw_legs[0].get("mode") if raw_legs else "Public Transit").title()
                        norm = RouteOptimizer.normalize_route(provider.provider_name, mode, itin, origin_name, dest_name, dist_km)
                        if norm:
                            all_routes.append(norm)

        # ── LEVEL 2: FlightProvider
        if scale in ["INTERNATIONAL", "INTERCONTINENTAL"] or (scale == "DOMESTIC" and dist_km > 500.0):
            flight_res = self.flight_provider.plan_journey(
                origin_lat, origin_lon, dest_lat, dest_lon, origin_name=origin_name, dest_name=dest_name
            )
            fl_status_str = flight_res.status.value if flight_res else "PROVIDER_UNAVAILABLE"
            fl_validation = validate_flight_result(flight_res)

            provider_trace.append({"provider": "FlightProvider", "status": fl_status_str, "note": fl_validation.get("reason", fl_validation.get("note", ""))})
            provider_audit["FlightProvider"] = {
                "configured": fl_status_str != "PROVIDER_NOT_CONFIGURED",
                "attempted": True,
                "status": "SUCCESS" if fl_validation.get("valid") else fl_status_str,
                "reason": fl_validation.get("reason", fl_validation.get("note", "")),
            }

            if fl_validation["valid"]:
                for itin in fl_validation["itineraries"]:
                    norm = RouteOptimizer.normalize_route("FlightProvider", "Flight", itin, origin_name, dest_name, dist_km)
                    if norm:
                        all_routes.append(norm)

        # ── LEVEL 3: OSRM Road Alternative
        road_alt = None
        osrm_dist = 0.0
        if scale in ["DOMESTIC", "SAME_CITY"] or (scale == "INTERNATIONAL" and dist_km < 1000.0):
            try:
                road_alt = OSRMRoadProvider.get_road_alternative(
                    origin_name, origin_lat, origin_lon, dest_name, dest_lat, dest_lon
                )
                if road_alt:
                    osrm_dist = road_alt.get("distance_km", 0.0)
            except Exception as e:
                logger.warning(f"[ROUTER V13.0] OSRM calculation failed: {e}")

        if road_alt and osrm_dist > 0:
            is_long_dist = False
            if scale in ["DOMESTIC", "SAME_CITY"] and osrm_dist > MAX_DOMESTIC_ROAD_DISTANCE_KM:
                is_long_dist = True
                
            road_alt["is_long_distance_fallback"] = is_long_dist
            norm = RouteOptimizer.normalize_route("OSRM", "Road", road_alt, origin_name, dest_name, osrm_dist)
            if norm:
                all_routes.append(norm)
                
            provider_trace.append({"provider": "OSRM", "status": "ROAD_ALTERNATIVE_ONLY" if is_long_dist else "SUCCESS"})
            provider_audit["OSRM"] = {
                "configured": True,
                "attempted": True,
                "status": "ROAD_ALTERNATIVE_ONLY" if is_long_dist else "SUCCESS",
                "reason": f"Road route ({osrm_dist} km)",
            }

        # ── OPTIMIZATION ──────────────────────────────
        optimized = RouteOptimizer.optimize(all_routes)

        if optimized and optimized.get("recommended_route"):
            route_options = optimized.get("route_options", [])
            has_transit = any(r.get("provider") not in ("OSRM", "FlightProvider") for r in route_options)
            has_rail = any(r.get("provider") == "RailRadar" for r in route_options)
            has_flight = any(r.get("provider") == "FlightProvider" for r in route_options)
            recommended_provider = optimized["recommended_route"]["provider"]

            if has_rail or has_transit:
                status = "MULTIMODAL_ROUTES_AVAILABLE"
                result_level = 1
            elif has_flight:
                status = "VERIFIED_FLIGHT"
                result_level = 2
            else:
                status = "VERIFIED_ROAD_ALTERNATIVE"
                result_level = 3
                
            # Build door-to-door journeys from the normalized routes
            journeys = []
            date_hint = (preferences or {}).get("date", "Tomorrow")
            try:
                journeys = stitch_all_journeys(
                    candidate_routes=optimized.get("route_options", []),
                    origin_name=origin_name,
                    origin_lat=origin_lat,
                    origin_lon=origin_lon,
                    dest_name=dest_name,
                    dest_lat=dest_lat,
                    dest_lon=dest_lon,
                    date_hint=date_hint,
                )
            except Exception as jb_err:
                logger.warning("[ROUTER] JourneyStitcher failed (non-fatal): %s", jb_err)

            return {
                "status": status,
                "result_level": result_level,
                "journey_scale": scale,
                "origin": origin_name,
                "destination": dest_name,
                "routes": optimized,
                "journeys": journeys,
                "route_guidance": None,
                "provider_trace": provider_trace,
                "provider_audit": provider_audit,
                "why_this_route": optimized.get("optimization", {}).get("why_this_route", ["Route optimized dynamically across all valid providers."]),
            }

        # ── LEVEL 4: AI Route Guidance
        guidance = AIRouteGuidanceService.generate_guidance(
            origin_name=origin_name,
            dest_name=dest_name,
            journey_scale=scale,
            origin_country=classification.get("origin_country", ""),
            dest_country=classification.get("destination_country", ""),
            provider_failures=provider_trace,
            distance_km=dist_km
        )

        if guidance:
            return {
                "status": "ROUTE_GUIDANCE_AVAILABLE",
                "result_level": 4,
                "journey_scale": scale,
                "origin": origin_name,
                "destination": dest_name,
                "routes": {},
                "route_guidance": guidance,
                "provider_trace": provider_trace,
                "provider_audit": provider_audit,
                "why_this_route": ["No verified providers available. Provided AI estimated route guidance."],
            }

        return {
            "status": "PROVIDERS_UNAVAILABLE",
            "result_level": 5,
            "journey_scale": scale,
            "origin": origin_name,
            "destination": dest_name,
            "routes": {},
            "route_guidance": None,
            "provider_trace": provider_trace,
            "provider_audit": provider_audit,
            "why_this_route": ["Providers unavailable for this route."],
            "message": f"Public transit could not be verified.",
        }
