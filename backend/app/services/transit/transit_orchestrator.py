"""
transit_orchestrator.py — WanderWise v12 Truth-First Multimodal Orchestrator

V12 Architecture:
  - Supports 5 Result Statuses: PUBLIC_TRANSIT_AVAILABLE, VERIFIED_ALTERNATIVE_AVAILABLE,
    ROUTE_GUIDANCE_AVAILABLE, ALTERNATIVE_PROVIDER_UNAVAILABLE, SAME_LOCATION.
  - Pre-routing SAME_LOCATION check (dist < 0.5 km).
  - Isolated AI Route Guidance payload under route_guidance object with verified=False.
  - Zero AI transit facts in journey legs.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from ..maps.nominatim_service import geocode_place
from ..weather.openmeteo_service import get_openmeteo_weather
from ..places.overpass_service import get_overpass_nearby, get_nearby_transit_infrastructure
from .transit_router import TransitRouter

logger = logging.getLogger(__name__)


def _format_money(amount: Optional[float], currency: str) -> str:
    """Formats monetary amounts with correct symbol. Never defaults to INR."""
    if amount is None:
        return "Fare unavailable"
    symbols = {
        "INR": "₹", "GBP": "£", "USD": "$", "EUR": "€",
        "JPY": "¥", "AUD": "A$", "SGD": "S$", "THB": "฿",
        "AED": "د.إ", "CAD": "C$", "KRW": "₩", "MYR": "RM",
    }
    sym = symbols.get(currency.upper() if currency else "", f"{currency} ")
    return f"{sym}{amount:,.2f}" if isinstance(amount, float) else f"{sym}{amount}"


class TransitOrchestrator:

    @staticmethod
    def get_transit_plan(
        origin: str,
        destination: str,
        origin_lat: Optional[float] = None,
        origin_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
        gps_accuracy: Optional[float] = None,
        preferred_mode: str = "fastest",
        budget: float = 5000.0,
        budget_currency: str = "INR",
        date: str = "Tomorrow",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        WanderWise v12 Multimodal Routing Orchestrator.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"

        # ── 1. Geocode Origin and Destination ─────────────────────────
        if origin_lat is not None and origin_lon is not None:
            geo_orig = {
                "lat": origin_lat,
                "lon": origin_lon,
                "display_name": origin if origin and origin != "Current Location" else "Current GPS Location",
                "source": "Browser Geolocation",
                "accuracy": gps_accuracy,
            }
        else:
            geo_orig = geocode_place(origin)

        if dest_lat is not None and dest_lon is not None:
            geo_dest = {
                "lat": dest_lat,
                "lon": dest_lon,
                "display_name": destination,
                "source": "Coordinates",
            }
        else:
            geo_dest = geocode_place(destination)

        orig_short = geo_orig["display_name"].split(",")[0]
        dest_short = geo_dest["display_name"].split(",")[0]

        logger.info(
            f"[TransitRequest V12] request_id={req_id} "
            f"origin_lat={geo_orig['lat']} origin_lon={geo_orig['lon']} "
            f"destination_lat={geo_dest['lat']} destination_lon={geo_dest['lon']} "
            f"origin_name='{orig_short}' destination_name='{dest_short}'"
        )

        # ── 2. Weather & Contextual Infrastructure ────────────────────
        weather_orig = get_openmeteo_weather(geo_orig["lat"], geo_orig["lon"], orig_short)
        weather_dest = get_openmeteo_weather(geo_dest["lat"], geo_dest["lon"], dest_short)
        orig_infra = get_nearby_transit_infrastructure(geo_orig["lat"], geo_orig["lon"])
        nearby_places = get_overpass_nearby(geo_dest["lat"], geo_dest["lon"])

        # ── 3. Execute V12 Router ─────────────────────────────────────
        router = TransitRouter()
        route_result = router.route(
            origin_name=orig_short,
            origin_lat=geo_orig["lat"],
            origin_lon=geo_orig["lon"],
            dest_name=dest_short,
            dest_lat=geo_dest["lat"],
            dest_lon=geo_dest["lon"],
        )

        status = route_result.get("status", "ROUTING_UNAVAILABLE")
        scale = route_result.get("journey_scale", "DOMESTIC")

        # Base response payload
        base_response = {
            "request_id": req_id,
            "status": status,
            "journey_scale": scale,
            "origin": orig_short,
            "destination": dest_short,
            "origin_coords": {"lat": geo_orig["lat"], "lon": geo_orig["lon"], "accuracy": gps_accuracy},
            "dest_coords": {"lat": geo_dest["lat"], "lon": geo_dest["lon"]},
            "preferred_mode": preferred_mode,
            "weather_obj": {
                "stops": [
                    {"location": orig_short, "temp": f"{weather_orig['temp_c']}°C", "icon": weather_orig["icon"]},
                    {"location": dest_short, "temp": f"{weather_dest['temp_c']}°C", "icon": weather_dest["icon"]},
                ]
            },
            "discovered_infrastructure": {
                "nearby_stations": orig_infra[:4] if orig_infra else [],
            },
            "nearby": nearby_places,
        }

        # ── 4. Handle SAME_LOCATION ──────────────────────────────────
        if status == "SAME_LOCATION":
            base_response.update({
                "journey": None,
                "road_alternative": None,
                "route_guidance": None,
                "same_location": True,
                "message": route_result.get("message"),
                "straight_line_distance_km": route_result.get("straight_line_distance_km", 0.0),
                "data_quality": {
                    "provider_engine": "Same Location Detection",
                    "schedule_timestamps": "N/A",
                    "platform_information": "N/A",
                    "distance_source": "Haversine Distance (<0.5 km)",
                    "walking_navigation": "N/A",
                    "geocoding_engine": geo_orig.get("source", "Nominatim / Geolocation"),
                    "ai_guidance": "Not used",
                },
            })
            return base_response

        # ── 5. Handle ROUTE_GUIDANCE_AVAILABLE (Level 3 AI Guidance) ──
        if status == "ROUTE_GUIDANCE_AVAILABLE":
            rg = route_result.get("route_guidance", {})
            base_response.update({
                "journey": None,
                "road_alternative": None,
                "route_guidance": rg,
                "provider_failures": route_result.get("provider_failures", []),
                "data_quality": {
                    "provider_engine": "None Available",
                    "schedule_timestamps": "Unavailable",
                    "platform_information": "Unavailable",
                    "distance_source": "Unavailable",
                    "walking_navigation": "N/A",
                    "geocoding_engine": geo_orig.get("source", "Nominatim / Geolocation"),
                    "ai_guidance": "Used for high-level structure only",
                },
                "provenance": {
                    "routing": "AI Route Guidance (Unverified)",
                    "geocoding": geo_orig.get("source", "Nominatim"),
                },
            })
            return base_response

        # ── 6. Handle ALTERNATIVE_PROVIDER_UNAVAILABLE (Level 4) ─────
        if status == "ALTERNATIVE_PROVIDER_UNAVAILABLE":
            base_response.update({
                "journey": None,
                "road_alternative": None,
                "route_guidance": None,
                "provider_failures": route_result.get("provider_failures", []),
                "message": route_result.get("message"),
                "data_quality": {
                    "provider_engine": "Flight Provider Unconfigured",
                    "schedule_timestamps": "Unavailable",
                    "platform_information": "Unavailable",
                    "distance_source": "Geographic Calculation",
                    "walking_navigation": "N/A",
                    "geocoding_engine": geo_orig.get("source", "Nominatim / Geolocation"),
                    "ai_guidance": "Not used",
                },
                "provenance": {
                    "routing": "Flight Provider Unconfigured",
                    "geocoding": geo_orig.get("source", "Nominatim"),
                },
            })
            return base_response

        # ── 7. Handle VERIFIED_ALTERNATIVE_AVAILABLE (Level 2) ────────
        if status == "VERIFIED_ALTERNATIVE_AVAILABLE":
            road_alt = route_result.get("road_alternative")
            base_response.update({
                "journey": route_result.get("journey"),
                "road_alternative": road_alt,
                "route_guidance": None,
                "provider_failures": route_result.get("provider_failures", []),
                "data_quality": {
                    "provider_engine": road_alt.get("provider", "OSRM Engine") if road_alt else "Flight Provider",
                    "schedule_timestamps": "Unavailable (Road/Flight Alternative)",
                    "platform_information": "Unavailable",
                    "distance_source": "OSRM Road Distance" if road_alt else "Provider Flight Distance",
                    "walking_navigation": "N/A",
                    "geocoding_engine": geo_orig.get("source", "Nominatim / Geolocation"),
                    "ai_guidance": "Not used",
                },
                "provenance": {
                    "routing": road_alt.get("provider", "OSRM") if road_alt else "Flight Provider",
                    "geocoding": geo_orig.get("source", "Nominatim"),
                },
            })
            return base_response

        # ── 8. Handle PUBLIC_TRANSIT_AVAILABLE (Level 1) ─────────────
        journey = route_result.get("journey", {})
        provider_name = route_result.get("provider_info", {}).get("provider", "Transitous")

        legs = journey.get("legs", [])
        transit_legs = [leg for leg in legs if leg.get("type") == "TRANSIT"]
        walk_legs = [leg for leg in legs if leg.get("type") == "WALK"]

        walking_dist_m = sum((leg.get("distance_m", 0) or 0) for leg in walk_legs)
        transit_dist_m = sum((leg.get("distance_m", 0) or 0) for leg in transit_legs)
        total_dist_m = walking_dist_m + transit_dist_m

        total_distance_km = round(total_dist_m / 1000.0, 1)
        walking_distance_km = round(walking_dist_m / 1000.0, 1)
        transit_distance_km = round(transit_dist_m / 1000.0, 1)

        transfers_cnt = max(0, len(transit_legs) - 1)
        journey["transfers"] = transfers_cnt

        total_duration_mins = journey.get("duration_minutes") or sum((leg.get("duration_minutes", 0) or 0) for leg in legs)
        movement_duration_mins = sum((leg.get("duration_minutes", 0) or 0) for leg in legs if leg.get("type") in ["TRANSIT", "WALK"])
        waiting_duration_mins = max(0, total_duration_mins - movement_duration_mins)

        journey["total_duration_minutes"] = total_duration_mins
        journey["movement_duration_minutes"] = movement_duration_mins
        journey["waiting_duration_minutes"] = waiting_duration_mins

        fare_obj = {
            "amount": None,
            "currency": "EUR" if "paris" in dest_short.lower() else "GBP",
            "source": provider_name,
            "status": "UNAVAILABLE",
            "display": "Fare unavailable",
        }

        journey["fare"] = fare_obj
        journey["distance_km"] = total_distance_km
        journey["walking_distance_km"] = walking_distance_km
        journey["transit_distance_km"] = transit_distance_km

        has_gtfs_timestamps = any(l.get("time_status") == "SCHEDULED" for l in transit_legs)
        has_platform_supplied = any(l.get("platform_source") == "PROVIDER" for l in transit_legs)
        has_haversine = any(l.get("distance_source") == "HAVERSINE" for l in transit_legs)

        data_quality = {
            "provider_engine": f"{provider_name} MOTIS",
            "schedule_timestamps": "GTFS Timestamps Verified" if has_gtfs_timestamps else "Schedule Unavailable",
            "platform_information": "Provider Supplied" if has_platform_supplied else "Unavailable",
            "distance_source": "Geographic Estimate" if has_haversine else "Provider Route Distance",
            "walking_navigation": "OSRM Foot Routing",
            "geocoding_engine": geo_orig.get("source", "Nominatim / Geolocation"),
            "ai_guidance": "Not used",
        }

        base_response.update({
            "status": "PUBLIC_TRANSIT_AVAILABLE",
            "journey": journey,
            "road_alternative": None,
            "route_guidance": None,
            "data_quality": data_quality,
            "recommended_mode": journey.get("actual_mode", "Public Transit"),
            "distance_km": total_distance_km,
            "walking_distance_km": walking_distance_km,
            "transit_distance_km": transit_distance_km,
            "travel_time": f"{total_duration_mins} min",
            "movement_time": f"{movement_duration_mins} min",
            "waiting_time": f"{waiting_duration_mins} min",
            "provider_info": route_result.get("provider_info"),
            "provenance": {
                "routing": f"{provider_name} GTFS",
                "weather": "Open-Meteo",
                "nearby": "OpenStreetMap Overpass",
                "geocoding": geo_orig.get("source", "Nominatim"),
            },
        })

        return base_response
