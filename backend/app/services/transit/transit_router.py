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
from .station_normalizer import normalize_station_name, normalize_mode_name

logger = logging.getLogger(__name__)

MAX_DOMESTIC_ROAD_DISTANCE_KM = 800.0

def validate_flight_result(result: ProviderResult) -> Dict[str, Any]:
    if not result or result.status != ProviderStatus.SUCCESS or not result.itineraries:
        reason_msg = (result.note or result.error) if result else "Flight provider returned no verified flight itinerary"
        category = getattr(result, "category", None) if result else None
        return {
            "valid": False,
            "reason": reason_msg,
            "category": category,
            "http_status": getattr(result, "http_status", None) if result else None,
        }

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

        origin_name = normalize_station_name(origin_name)
        dest_name = normalize_station_name(dest_name)

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
                "routes": {},
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

        # ── LEVEL 1-3: Concurrent Multimodal Provider Execution ───────────
        provider_prefs = dict(preferences or {})
        provider_prefs["origin_name"] = origin_name
        provider_prefs["dest_name"] = dest_name

        from .provider_manager import ProviderManager
        mgr = ProviderManager.get_instance()

        mgr_res = mgr.query_providers(
            origin_name=origin_name,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_name=dest_name,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            departure_time=departure_time,
            preferences=provider_prefs,
            scale=scale,
            dist_km=dist_km,
        )

        all_routes = []
        provider_trace = []
        provider_audit = {}

        # 1. Normalize transit and flight itineraries with destination identity validation
        for itin in mgr_res.get("itineraries", []):
            prov = itin.get("provider", "TransitProvider")
            raw_legs = itin.get("legs", [])
            default_mode = itin.get("mode") or (raw_legs[0].get("mode") if raw_legs else "Public Transit")
            norm = RouteOptimizer.normalize_route(
                prov, default_mode, itin, origin_name, dest_name, dist_km,
                departure_time=departure_time,
                origin_lat=origin_lat, origin_lon=origin_lon,
                dest_lat=dest_lat, dest_lon=dest_lon
            )
            if norm:
                all_routes.append(norm)

        # 2. Road alternative
        road_alt = mgr_res.get("road_alternative")
        if road_alt:
            osrm_dist = road_alt.get("distance_km", dist_km)
            is_long_dist = False
            if scale in ["DOMESTIC", "SAME_CITY"] and osrm_dist > MAX_DOMESTIC_ROAD_DISTANCE_KM:
                is_long_dist = True
            road_alt["is_long_distance_fallback"] = is_long_dist
            norm_road = RouteOptimizer.normalize_route(
                "OSRM", "Driving", road_alt, origin_name, dest_name, osrm_dist,
                departure_time=departure_time,
                origin_lat=origin_lat, origin_lon=origin_lon,
                dest_lat=dest_lat, dest_lon=dest_lon
            )
            if norm_road:
                all_routes.append(norm_road)

        # 3. Populate provider audit & statuses
        provider_statuses = mgr_res.get("provider_statuses", {})
        results_by_prov = mgr_res.get("results_by_provider", {})
        for p_name, p_status_str in provider_statuses.items():
            p_res = results_by_prov.get(p_name)
            p_stat_val = p_res.status.value if (p_res and p_res.status) else "UNAVAILABLE"
            provider_trace.append({"provider": p_name, "status": p_status_str, "note": getattr(p_res, "note", None)})
            provider_audit[p_name] = {
                "configured": p_stat_val != "PROVIDER_NOT_CONFIGURED",
                "attempted": True,
                "status": p_status_str,
                "reason": (p_res.error or p_res.note) if p_res else p_status_str,
                "latency_ms": getattr(p_res, "latency_ms", None) if p_res else None,
                "rate_limit_info": getattr(p_res, "rate_limit_info", None) if p_res else None,
            }

        # 4. Evaluate any custom transit providers dynamically attached to router
        standard_names = {"RailRadar", "Transitous", "RailwayEngine", "QRail", "IndianRailways-ScheduleVerified"}
        custom_providers = [p for p in getattr(self, "transit_providers", []) if getattr(p, "provider_name", "") not in standard_names]
        for cp in custom_providers:
            c_name = getattr(cp, "provider_name", "CustomProvider")
            try:
                c_res = cp.plan_journey(origin_lat, origin_lon, dest_lat, dest_lon, departure_time, provider_prefs)
                c_stat = c_res.status.value if (isinstance(c_res, ProviderResult) and c_res.status) else "SUCCESS"
                c_reason = c_res.error or c_res.note if isinstance(c_res, ProviderResult) else "Completed"
            except Exception as ce:
                c_stat = "PROVIDER_UNAVAILABLE"
                c_reason = str(ce)
            provider_trace.append({"provider": c_name, "status": c_stat, "note": c_reason})
            provider_audit[c_name] = {
                "configured": True,
                "attempted": True,
                "status": c_stat,
                "reason": c_reason,
            }

        # ── OPTIMIZATION ──────────────────────────────
        req_time = (preferences or {}).get("request_time") or departure_time
        optimized = RouteOptimizer.optimize(all_routes, request_time=req_time)

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
            date_hint = (preferences or {}).get("date", "Today")
            try:
                journeys = stitch_all_journeys(
                    candidate_routes=optimized.get("route_options", []),
                    origin_name=origin_name,
                    origin_lat=origin_lat,
                    origin_lon=origin_lon,
                    dest_name=dest_name,
                    dest_lat=dest_lat,
                    dest_lon=dest_lon,
                    request_time=req_time,
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
                "recommended_route": optimized.get("recommended_route"),
                "journeys": journeys,
                "route_guidance": None,
                "provider_trace": provider_trace,
                "provider_audit": provider_audit,
                "provider_statuses": provider_statuses,
                "message": mgr_res.get("message"),
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
            rec_m = (guidance.get("recommended_mode") or "").lower()
            if "flight" in rec_m:
                no_itinerary_msg = "No verified flight itinerary available for selected date."
            elif "rail" in rec_m or "train" in rec_m:
                no_itinerary_msg = "No verified train itinerary available for selected date."
            else:
                no_itinerary_msg = "No verified transit itineraries available for selected date."

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
                "provider_statuses": provider_statuses,
                "message": no_itinerary_msg,
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
            "provider_statuses": provider_statuses,
            "why_this_route": ["Providers unavailable for this route."],
            "message": mgr_res.get("message") or "No verified transit routes available.",
        }
