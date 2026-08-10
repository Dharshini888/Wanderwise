"""
transit_router.py — WanderWise Transit V12.2 Provider Priority Router with Provider Trace & Rail Integration

V12.2 Result Hierarchy:
  Level 0: SAME_LOCATION (dist < 0.5 km)
  Level 1: PUBLIC_TRANSIT_AVAILABLE (Transitous, Navitia, RailRadar, IndiaTransit, GTFSLocal)
  Level 2: VERIFIED_ALTERNATIVE_AVAILABLE (RailRadar, FlightProvider, OSRM Driving for domestic/short intl <1000 km)
  Level 3: ROUTE_GUIDANCE_AVAILABLE (Unverified high-level AI travel guidance structure)
  Level 4: ALTERNATIVE_PROVIDER_UNAVAILABLE (Provider unconfigured or unreachable)
"""

import logging
from typing import Dict, Any, Optional, List
from .journey_classifier import JourneyClassifier
from .ai_route_guidance import AIRouteGuidanceService
from .itinerary_validator import validate_itinerary
from .providers.base import ProviderStatus, ProviderResult
from .providers.transitous_provider import TransitousProvider
from .providers.navitia_provider import NavitiaProvider
from .providers.railradar_provider import RailRadarProvider
from .providers.india_transit_provider import IndiaTransitProvider
from .providers.gtfs_provider import GTFSLocalProvider
from .providers.osrm_provider import OSRMRoadProvider
from .providers.flight_provider import FlightProvider
from ..location.location_normalizer import check_location_sanity

logger = logging.getLogger(__name__)


class TransitRouter:
    def __init__(self):
        self.transit_providers = [
            TransitousProvider(),
            NavitiaProvider(),
            RailRadarProvider(),
            IndiaTransitProvider(),
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
        Executes V12.2 Multimodal Priority Router pipeline with provider tracing and strict itinerary validation.
        """
        provider_trace: List[Dict[str, Any]] = []

        # ── 0. Location Sanity & SAME_LOCATION Check ──────────────────
        orig_dict = {"name": origin_name, "lat": origin_lat, "lon": origin_lon}
        dest_dict = {"name": dest_name, "lat": dest_lat, "lon": dest_lon}
        sanity = check_location_sanity(orig_dict, dest_dict)

        if sanity.get("same_location"):
            logger.info(f"[ROUTER V12.2] SAME_LOCATION triggered ({origin_name} -> {dest_name})")
            return {
                "status": "SAME_LOCATION",
                "journey_scale": "SAME_LOCATION",
                "journey": None,
                "road_alternative": None,
                "route_guidance": None,
                "same_location": True,
                "provider_trace": provider_trace,
                "message": f"Origin '{origin_name}' and destination '{dest_name}' are within 500 meters of each other.",
                "straight_line_distance_km": sanity.get("straight_line_distance_km", 0.0),
            }

        # Classify journey scale
        classification = JourneyClassifier.classify(
            origin_lat, origin_lon, dest_lat, dest_lon, origin_name, dest_name
        )
        scale = classification.get("scale", "DOMESTIC")
        dist_km = classification.get("distance_km", 0)

        # ── LEVEL 1: Evaluate Public Transit & Rail Providers ───────────
        for provider in self.transit_providers:
            logger.info(f"[ROUTER V12.2] Evaluating provider: {provider.provider_name}")
            try:
                result: ProviderResult = provider.plan_journey(
                    origin_lat, origin_lon, dest_lat, dest_lon, departure_time, preferences
                )
            except Exception as e:
                logger.warning(f"[ROUTER V12.2] Provider {provider.provider_name} raised exception: {e}")
                result = ProviderResult(
                    status=ProviderStatus.PROVIDER_UNAVAILABLE,
                    provider_name=provider.provider_name,
                    error=str(e)[:150],
                )

            p_status_str = result.status.value if (result and result.status) else "PROVIDER_UNAVAILABLE"
            provider_trace.append({
                "provider": provider.provider_name,
                "status": p_status_str,
                "note": result.note if result else None,
            })

            if result and result.status == ProviderStatus.SUCCESS and result.itineraries:
                valid_itinerary = None
                validation_report = None

                for itin in result.itineraries:
                    v_report = validate_itinerary(itin)
                    if v_report.get("valid"):
                        valid_itinerary = itin
                        validation_report = v_report
                        break
                    else:
                        logger.warning(f"[ROUTER V12.2] Itinerary from {provider.provider_name} rejected by validator: {v_report.get('errors')}")

                if valid_itinerary:
                    logger.info(f"[ROUTER V12.2] Level 1 Success via provider: {provider.provider_name}")
                    raw_legs = valid_itinerary.get("legs", [])

                    # Normalize boarding walk legs via OSRM
                    first_transit_leg = next(
                        (leg for leg in raw_legs if leg.get("type") == "TRANSIT"), None
                    )
                    normalized_legs = []

                    if first_transit_leg and first_transit_leg.get("boarding_stop"):
                        board_stop = first_transit_leg["boarding_stop"]
                        board_lat = board_stop.get("lat")
                        board_lon = board_stop.get("lon")

                        if board_lat and board_lon and (
                            abs(board_lat - origin_lat) > 0.0001 or abs(board_lon - origin_lon) > 0.0001
                        ):
                            gps_walk_leg = OSRMRoadProvider.get_walking_leg(
                                from_name=origin_name,
                                from_lat=origin_lat,
                                from_lon=origin_lon,
                                to_name=board_stop.get("name") or "Boarding Station",
                                to_lat=board_lat,
                                to_lon=board_lon,
                            )
                            normalized_legs.append(gps_walk_leg)

                    for leg in raw_legs:
                        if leg.get("type") == "WALK" and normalized_legs and normalized_legs[0]["type"] == "WALK":
                            continue
                        normalized_legs.append(leg)

                    last_transit_leg = next(
                        (leg for leg in reversed(raw_legs) if leg.get("type") == "TRANSIT"), None
                    )
                    if last_transit_leg and last_transit_leg.get("alighting_stop"):
                        alight_stop = last_transit_leg["alighting_stop"]
                        alight_lat = alight_stop.get("lat")
                        alight_lon = alight_stop.get("lon")
                        if alight_lat and alight_lon and (
                            abs(alight_lat - dest_lat) > 0.0001 or abs(alight_lon - dest_lon) > 0.0001
                        ):
                            last_walk_leg = OSRMRoadProvider.get_walking_leg(
                                from_name=alight_stop.get("name") or "Alighting Station",
                                from_lat=alight_lat,
                                from_lon=alight_lon,
                                to_name=dest_name,
                                to_lat=dest_lat,
                                to_lon=dest_lon,
                            )
                            normalized_legs.append(last_walk_leg)

                    transit_modes = [
                        leg["mode"] for leg in normalized_legs
                        if leg.get("type") == "TRANSIT" and leg.get("mode")
                    ]
                    actual_mode = transit_modes[0].title() if transit_modes else "Public Transit"

                    journey_obj = {
                        "origin": {"name": origin_name, "lat": origin_lat, "lon": origin_lon},
                        "destination": {"name": dest_name, "lat": dest_lat, "lon": dest_lon},
                        "departure_time": valid_itinerary.get("departure_time"),
                        "arrival_time": valid_itinerary.get("arrival_time"),
                        "duration_minutes": valid_itinerary.get("duration_minutes"),
                        "transfers": valid_itinerary.get("transfers", 0),
                        "actual_mode": actual_mode,
                        "provider": provider.provider_name,
                        "legs": normalized_legs,
                        "validation": validation_report,
                    }

                    return {
                        "status": "PUBLIC_TRANSIT_AVAILABLE",
                        "journey_scale": scale,
                        "journey": journey_obj,
                        "road_alternative": None,
                        "route_guidance": None,
                        "provider_trace": provider_trace,
                        "provider_info": {
                            "provider": provider.provider_name,
                            "status": "SUCCESS",
                        },
                    }

        # ── LEVEL 2: Verified Alternative Providers (Flight / OSRM) ─────
        logger.info(f"[ROUTER V12.2] Level 1 Transit failed. Evaluating Level 2 Verified Alternatives (scale={scale}, dist={dist_km}km).")

        # Evaluate FlightProvider for International or Intercontinental
        if scale in ["INTERNATIONAL", "INTERCONTINENTAL"]:
            flight_res = self.flight_provider.plan_journey(origin_lat, origin_lon, dest_lat, dest_lon)
            provider_trace.append({
                "provider": "FlightProvider",
                "status": flight_res.status.value,
                "note": flight_res.note or "Flight provider evaluated.",
            })

            if flight_res.status == ProviderStatus.SUCCESS and flight_res.itineraries:
                logger.info("[ROUTER V12.2] Level 2 Verified Flight Alternative available!")
                return {
                    "status": "VERIFIED_ALTERNATIVE_AVAILABLE",
                    "journey_scale": scale,
                    "journey": {
                        "provider": flight_res.provider_name,
                        "actual_mode": "Flight",
                        "itineraries": flight_res.itineraries,
                    },
                    "road_alternative": None,
                    "route_guidance": None,
                    "provider_trace": provider_trace,
                }

            # Evaluate OSRM road alternative ONLY for INTERNATIONAL routes < 1000 km
            if scale == "INTERNATIONAL" and dist_km < 1000:
                try:
                    road_alt = OSRMRoadProvider.get_road_alternative(
                        origin_name, origin_lat, origin_lon,
                        dest_name, dest_lat, dest_lon
                    )
                    if road_alt and (road_alt.get("distance_km") or 0) > 0:
                        logger.info("[ROUTER V12.2] Level 2 Verified OSRM Road Alternative available (Short International).")
                        provider_trace.append({"provider": "OSRM", "status": "SUCCESS"})
                        road_alt["alternative_type"] = "ROAD"
                        road_alt["provider"] = "OSRM"
                        road_alt["verified"] = True
                        road_alt["schedule_verified"] = False
                        road_alt["route_type"] = "ROAD_DRIVING"
                        return {
                            "status": "VERIFIED_ALTERNATIVE_AVAILABLE",
                            "journey_scale": scale,
                            "journey": None,
                            "road_alternative": road_alt,
                            "route_guidance": None,
                            "provider_trace": provider_trace,
                        }
                except Exception as e:
                    logger.warning(f"[ROUTER V12.2] OSRM international road alternative failed: {e}")

        # Domestic / Same City OSRM Road Alternative
        elif scale in ["DOMESTIC", "SAME_CITY"]:
            try:
                road_alt = OSRMRoadProvider.get_road_alternative(
                    origin_name, origin_lat, origin_lon,
                    dest_name, dest_lat, dest_lon
                )
                if road_alt and (road_alt.get("distance_km") or 0) > 0:
                    logger.info("[ROUTER V12.2] Level 2 Verified OSRM Road Alternative available (Domestic).")
                    provider_trace.append({"provider": "OSRM", "status": "SUCCESS"})
                    road_alt["alternative_type"] = "ROAD"
                    road_alt["provider"] = "OSRM"
                    road_alt["verified"] = True
                    road_alt["schedule_verified"] = False
                    road_alt["route_type"] = "ROAD_DRIVING"
                    return {
                        "status": "VERIFIED_ALTERNATIVE_AVAILABLE",
                        "journey_scale": scale,
                        "journey": None,
                        "road_alternative": road_alt,
                        "route_guidance": None,
                        "provider_trace": provider_trace,
                    }
            except Exception as e:
                logger.warning(f"[ROUTER V12.2] OSRM domestic road alternative failed: {e}")

        # ── LEVEL 3: AI Route Guidance (Unverified High-Level Structure) ─
        logger.info(f"[ROUTER V12.2] Level 1 & Level 2 failed. Generating Level 3 AI Route Guidance.")
        guidance = AIRouteGuidanceService.generate_guidance(
            origin_name=origin_name,
            dest_name=dest_name,
            journey_scale=scale,
            origin_country=classification.get("origin_country", ""),
            dest_country=classification.get("destination_country", ""),
            provider_failures=provider_trace,
        )

        if guidance and guidance.get("verified") is False and guidance.get("steps"):
            return {
                "status": "ROUTE_GUIDANCE_AVAILABLE",
                "journey_scale": scale,
                "journey": None,
                "road_alternative": None,
                "route_guidance": guidance,
                "provider_trace": provider_trace,
            }

        # ── LEVEL 4: Alternative Provider Unavailable ──────────────────
        logger.info("[ROUTER V12.2] Returning Level 4 ALTERNATIVE_PROVIDER_UNAVAILABLE.")
        return {
            "status": "ALTERNATIVE_PROVIDER_UNAVAILABLE",
            "journey_scale": scale,
            "journey": None,
            "road_alternative": None,
            "route_guidance": None,
            "provider_trace": provider_trace,
            "message": f"Public transit and verified alternatives could not be verified for this {scale.lower()} journey.",
        }
