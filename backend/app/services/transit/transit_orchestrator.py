"""
transit_orchestrator.py — WanderWise v12.3 Truth-First Multimodal Orchestrator

V12.3 Architecture:
  - Supports 6 Result Hierarchy Levels: SAME_LOCATION, PUBLIC_TRANSIT_AVAILABLE, VERIFIED_FLIGHT,
    VERIFIED_ROAD_ALTERNATIVE, ROUTE_GUIDANCE_AVAILABLE, PROVIDERS_UNAVAILABLE.
  - Validates coordinate-to-city sanity to prevent stale browser GPS coordinates from corrupting explicit city searches.
  - Strictly enforces 5.0 km geographic distance boundaries for all nearby boarding points.
  - Exposes origin_source ("BROWSER_GPS" vs "GEOCODED_LOCATION") in nearby_provenance.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from ..maps.nominatim_service import geocode_place
from ..maps.osrm_service import haversine_distance
from ..weather.openmeteo_service import get_openmeteo_weather
from ..places.overpass_service import get_overpass_nearby, get_nearby_boarding_infrastructure
from .transit_router import TransitRouter
from .live_transit_service import LiveTransitService
from .station_normalizer import normalize_station_name, normalize_mode_name, get_mode_icon

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
        origin_source: Optional[str] = None,
        origin_lat: Optional[float] = None,
        origin_lon: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lon: Optional[float] = None,
        gps_accuracy: Optional[float] = None,
        origin_accuracy_m: Optional[float] = None,
        preferred_mode: str = "fastest",
        budget: float = 5000.0,
        budget_currency: str = "INR",
        date: str = "Today",
        departure_type: str = "now",
        departure_time: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        WanderWise v12.3 Multimodal Routing Orchestrator with Departure-Time Awareness.
        """
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        acc = origin_accuracy_m if origin_accuracy_m is not None else gps_accuracy

        # ── 1. Geocode Origin and Destination with Strict Coordinate Precedence & Sanity ──
        valid_origin_coords = (
            origin_lat is not None and origin_lon is not None
            and isinstance(origin_lat, (int, float)) and isinstance(origin_lon, (int, float))
            and -90.0 <= origin_lat <= 90.0 and -180.0 <= origin_lon <= 180.0
            and not (origin_lat == 0.0 and origin_lon == 0.0)
        )

        is_gps_origin_text = bool(origin and any(k in origin.lower() for k in ["current", "location", "gps", "home city"]))

        # Destination resolution with coordinate-to-city sanity check
        valid_dest_coords = (
            dest_lat is not None and dest_lon is not None
            and isinstance(dest_lat, (int, float)) and isinstance(dest_lon, (int, float))
            and -90.0 <= dest_lat <= 90.0 and -180.0 <= dest_lon <= 180.0
            and not (dest_lat == 0.0 and dest_lon == 0.0)
        )

        expected_dest = geocode_place(destination) if destination else None
        if valid_dest_coords and expected_dest and expected_dest.get("lat") is not None and expected_dest.get("lon") is not None:
            # Check geographic distance between provided coords and geocoded destination
            dest_drift_km = haversine_distance(float(dest_lat), float(dest_lon), float(expected_dest["lat"]), float(expected_dest["lon"]))
            if dest_drift_km > 50.0:
                logger.warning(
                    f"[TRANSIT][COORDINATE_SANITY_FAIL] Provided dest_coords ({dest_lat}, {dest_lon}) are {dest_drift_km:.1f} km "
                    f"away from geocoded '{destination}' ({expected_dest['lat']}, {expected_dest['lon']}). Discarding stale coordinates."
                )
                geo_dest = expected_dest
            else:
                geo_dest = {
                    "lat": float(dest_lat),
                    "lon": float(dest_lon),
                    "display_name": expected_dest.get("display_name") or destination,
                    "source": "Coordinates",
                    "country_code": expected_dest.get("country_code"),
                }
        elif valid_dest_coords:
            geo_dest = {
                "lat": float(dest_lat),
                "lon": float(dest_lon),
                "display_name": destination,
                "source": "Coordinates",
            }
        else:
            geo_dest = expected_dest

        # Origin resolution with coordinate-to-city sanity check
        if is_gps_origin_text or origin_source == "BROWSER_GPS":
            resolved_origin_source = "BROWSER_GPS"
            if valid_origin_coords:
                geo_orig = {
                    "lat": float(origin_lat),
                    "lon": float(origin_lon),
                    "display_name": origin or "Current GPS Location",
                    "source": "Browser GPS",
                    "accuracy": acc,
                }
            else:
                geo_orig = None
        else:
            expected_orig = geocode_place(origin) if origin else None
            if valid_origin_coords and expected_orig and expected_orig.get("lat") is not None and expected_orig.get("lon") is not None:
                orig_drift_km = haversine_distance(float(origin_lat), float(origin_lon), float(expected_orig["lat"]), float(expected_orig["lon"]))
                if orig_drift_km > 50.0:
                    logger.warning(
                        f"[TRANSIT][COORDINATE_SANITY_FAIL] Provided origin_coords ({origin_lat}, {origin_lon}) are {orig_drift_km:.1f} km "
                        f"away from geocoded '{origin}' ({expected_orig['lat']}, {expected_orig['lon']}). Discarding stale coordinates."
                    )
                    geo_orig = expected_orig
                    resolved_origin_source = "GEOCODED_LOCATION"
                else:
                    geo_orig = {
                        "lat": float(origin_lat),
                        "lon": float(origin_lon),
                        "display_name": expected_orig.get("display_name") or origin,
                        "source": origin_source or "ACTIVITY_COORDINATES",
                        "accuracy": acc,
                        "country_code": expected_orig.get("country_code"),
                    }
                    resolved_origin_source = origin_source or "ACTIVITY_COORDINATES"
            elif valid_origin_coords:
                resolved_origin_source = origin_source or "ACTIVITY_COORDINATES"
                geo_orig = {
                    "lat": float(origin_lat),
                    "lon": float(origin_lon),
                    "display_name": origin,
                    "source": "Itinerary Coordinates",
                    "accuracy": acc,
                }
            else:
                resolved_origin_source = "GEOCODED_LOCATION"
                geo_orig = expected_orig

        orig_has_coords = geo_orig and geo_orig.get("lat") is not None and geo_orig.get("lon") is not None
        dest_has_coords = geo_dest and geo_dest.get("lat") is not None and geo_dest.get("lon") is not None

        if not orig_has_coords or not dest_has_coords:
            logger.warning(f"[TRANSIT] Route failed: Unable to resolve coordinates for origin='{origin}' or dest='{destination}'")
            return {
                "status": "LOCATION_UNRESOLVED",
                "result_level": 5,
                "journey_scale": "UNRESOLVED",
                "origin": origin,
                "destination": destination,
                "routes": [],
                "route_guidance": None,
                "message": f"Unable to determine location coordinates for '{origin if not orig_has_coords else destination}'.",
                "recommended_route": None,
            }

        orig_short = normalize_station_name(geo_orig["display_name"].split(",")[0] if geo_orig else (origin or "Current GPS Location"))
        dest_short = normalize_station_name(geo_dest["display_name"].split(",")[0])

        # ── 2. Weather & Contextual Infrastructure (Concurrent & Non-blocking) ──
        weather_orig = {"temp_c": "--", "weather_code": "unknown", "icon": "☀️"}
        weather_dest = {"temp_c": "--", "weather_code": "unknown", "icon": "☀️"}
        nearby_places = []

        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="transit_enrich") as enrich_pool:
            fut_w_orig = enrich_pool.submit(get_openmeteo_weather, geo_orig["lat"], geo_orig["lon"], orig_short)
            fut_w_dest = enrich_pool.submit(get_openmeteo_weather, geo_dest["lat"], geo_dest["lon"], dest_short)
            fut_nearby = enrich_pool.submit(get_overpass_nearby, geo_dest["lat"], geo_dest["lon"])

            try:
                w_o = fut_w_orig.result(timeout=1.2)
                if w_o:
                    weather_orig = w_o
            except Exception as e:
                logger.debug(f"[TRANSIT] Weather orig skipped/timed out: {e}")

            try:
                w_d = fut_w_dest.result(timeout=1.2)
                if w_d:
                    weather_dest = w_d
            except Exception as e:
                logger.debug(f"[TRANSIT] Weather dest skipped/timed out: {e}")

            try:
                nb = fut_nearby.result(timeout=1.2)
                if nb:
                    nearby_places = nb
            except Exception as e:
                logger.debug(f"[TRANSIT] Overpass POI skipped/timed out: {e}")

        router_orig_lat = geo_orig["lat"]
        router_orig_lon = geo_orig["lon"]

        # ── 3. Resolve Planning Date & Departure Time ──────────────────
        from datetime import date as date_cls, datetime, time as time_cls, timedelta
        import os

        from .tz_utils import get_timezone
        tz_name = os.getenv("TRANSIT_TIMEZONE", "Asia/Kolkata")
        local_tz = get_timezone(tz_name)

        now_local = datetime.now(local_tz) if local_tz else datetime.now()
        today_date = now_local.date()

        d_str = str(date or "").strip().lower()
        if d_str in ("tomorrow", "next day"):
            planning_date = today_date + timedelta(days=1)
        elif d_str in ("today", "now"):
            planning_date = today_date
        elif d_str:
            try:
                planning_date = datetime.strptime(d_str.split()[0], "%Y-%m-%d").date()
            except Exception:
                planning_date = today_date
        else:
            planning_date = today_date

        parsed_time = None
        dep_type_clean = str(departure_type or "now").strip().lower()
        t_str = str(departure_time or "").strip()

        if t_str and t_str.lower() not in ("now", "none", "null", ""):
            try:
                iso_dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                parsed_time = iso_dt.time()
                if not date or str(date).strip().lower() in ("today", "now"):
                    planning_date = iso_dt.date()
            except Exception:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p", "%H:%M:%S"):
                    try:
                        parsed_time = datetime.strptime(t_str, fmt).time()
                        break
                    except Exception:
                        pass
        elif dep_type_clean == "now":
            parsed_time = now_local.time()
            planning_date = today_date

        if not parsed_time:
            parsed_time = now_local.time() if planning_date == today_date else time_cls(8, 0)

        req_dep_dt = datetime.combine(planning_date, parsed_time)
        if local_tz:
            req_dep_dt = req_dep_dt.replace(tzinfo=local_tz)

        departure_time_iso = req_dep_dt.isoformat()

        # ── 4. Execute Router ─────────────────────────────────────────
        all_route_options = []
        journeys_list = []
        router = TransitRouter()
        route_result = router.route(
            origin_name=orig_short,
            origin_lat=router_orig_lat,
            origin_lon=router_orig_lon,
            dest_name=dest_short,
            dest_lat=geo_dest["lat"],
            dest_lon=geo_dest["lon"],
            departure_time=departure_time_iso,
            preferences={
                "date": date,
                "departure_type": departure_type,
                "departure_time": departure_time,
                "request_time": req_dep_dt,
                "preferred_mode": preferred_mode,
                "budget": budget,
                "full_origin_name": geo_orig["display_name"] if geo_orig else origin,
                "full_dest_name": geo_dest["display_name"] if geo_dest else destination,
            },
        )

        status = route_result.get("status", "ROUTING_UNAVAILABLE")
        # Normalize MULTIMODAL_ROUTES_AVAILABLE → PUBLIC_TRANSIT_AVAILABLE for internal handling
        if status == "MULTIMODAL_ROUTES_AVAILABLE":
            status = "PUBLIC_TRANSIT_AVAILABLE"
        scale = route_result.get("journey_scale", "DOMESTIC")
        provider_audit = route_result.get("provider_audit", {})
        why_this_route = route_result.get("why_this_route", [])
        result_level = route_result.get("result_level", 4)

        # Truth-First Verification Flag
        is_verified = status in ["PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_FLIGHT", "VERIFIED_ROAD_ALTERNATIVE"]
        
        raw_routes_early = route_result.get("routes")
        if isinstance(raw_routes_early, dict):
            opt = raw_routes_early
        elif isinstance(raw_routes_early, list):
            opt = {
                "recommended_route": raw_routes_early[0] if raw_routes_early else None,
                "route_options": raw_routes_early
            }
        else:
            opt = {}
        journey = opt.get("recommended_route") or {}
        all_route_options = opt.get("route_options", [])  # All 7+ trains + OSRM
        journeys_list = route_result.get("journeys", [])
        
        # ── Determine Best Boarding Point ─────────────────────────────
        boarding_name = None
        boarding_lat = None
        boarding_lon = None
        boarding_source = None
        reference_type = "unknown"

        if status in ["PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_FLIGHT"] and journey.get("legs"):
            first_leg = journey["legs"][0]
            b_stop = first_leg.get("boarding_stop", {})
            if b_stop.get("name") and b_stop.get("lat") and b_stop.get("lon"):
                boarding_name = b_stop["name"]
                boarding_lat = b_stop["lat"]
                boarding_lon = b_stop["lon"]
                boarding_source = journey.get("provider", "Verified Provider")
                reference_type = "actual_boarding_point"
            elif first_leg.get("from_name") and first_leg.get("from_lat") and first_leg.get("from_lon"):
                boarding_name = first_leg["from_name"]
                boarding_lat = first_leg["from_lat"]
                boarding_lon = first_leg["from_lon"]
                boarding_source = journey.get("provider", "Verified Provider")
                reference_type = "actual_boarding_point"

        if reference_type == "actual_boarding_point":
            nearby_ref_lat = float(boarding_lat)
            nearby_ref_lon = float(boarding_lon)
            nearby_prov = {
                "reference_type": "actual_boarding_point",
                "reference_name": boarding_name,
                "latitude": nearby_ref_lat,
                "longitude": nearby_ref_lon,
                "source": boarding_source,
                "verified": True
            }
        elif geo_orig and resolved_origin_source == "BROWSER_GPS":
            nearby_ref_lat = float(geo_orig["lat"])
            nearby_ref_lon = float(geo_orig["lon"])
            nearby_prov = {
                "reference_type": "origin_coords_gps",
                "reference_name": "Current Location",
                "latitude": nearby_ref_lat,
                "longitude": nearby_ref_lon,
                "source": "Browser GPS",
                "verified": True
            }
        elif geo_orig:
            nearby_ref_lat = float(geo_orig["lat"])
            nearby_ref_lon = float(geo_orig["lon"])
            nearby_prov = {
                "reference_type": "origin_city_fallback",
                "reference_name": geo_orig["display_name"],
                "latitude": nearby_ref_lat,
                "longitude": nearby_ref_lon,
                "source": "Geocoding",
                "verified": False
            }
        else:
            nearby_ref_lat = float(router_orig_lat)
            nearby_ref_lon = float(router_orig_lon)
            nearby_prov = {
                "reference_type": "default_fallback",
                "reference_name": "Default Fallback",
                "latitude": nearby_ref_lat,
                "longitude": nearby_ref_lon,
                "source": "System Default",
                "verified": False
            }
            
        logger.info(f"[TRANSIT][NEARBY] reference_type={nearby_prov['reference_type']} reference_name={nearby_prov['reference_name']} lat={nearby_ref_lat} lon={nearby_ref_lon} source={nearby_prov['source']}")

        if geo_orig or reference_type == "actual_boarding_point":
            try:
                with ThreadPoolExecutor(max_workers=1, thread_name_prefix="transit_infra") as infra_pool:
                    fut_infra = infra_pool.submit(
                        get_nearby_boarding_infrastructure,
                        nearby_ref_lat,
                        nearby_ref_lon,
                        radius_m=5000,
                        origin_source=resolved_origin_source,
                        gps_accuracy_m=acc,
                    )
                    infra_res = fut_infra.result(timeout=1.0)
            except Exception as e:
                logger.debug(f"[TRANSIT] Boarding infra timed out/failed, using verified fallback: {e}")
                from app.services.places.overpass_service import _get_local_verified_hubs
                local_hubs = _get_local_verified_hubs(nearby_ref_lat, nearby_ref_lon, max_radius_km=5.0)
                infra_res = {
                    "items": local_hubs,
                    "provenance": {
                        "provider": "Verified Transit Infrastructure",
                        "origin_source": resolved_origin_source,
                        "origin_lat": nearby_ref_lat,
                        "origin_lon": nearby_ref_lon,
                        "origin_accuracy_m": acc,
                        "radius_km": 5.0,
                        "queried": True,
                        "fallback_used": True,
                        "fallback_reason": "Live query deadline exceeded; instant verified fallback used",
                        "result_count": len(local_hubs),
                    }
                }
            raw_nearby = infra_res.get("items", [])
            infra_res["provenance"] = nearby_prov
            nearby_provenance = nearby_prov
            
            formatted_nearby = []
            for item in raw_nearby:
                p_lat = item.get("latitude") if item.get("latitude") is not None else item.get("lat")
                p_lon = item.get("longitude") if item.get("longitude") is not None else item.get("lon")
                if p_lat is not None and p_lon is not None:
                    calc_dist = haversine_distance(nearby_ref_lat, nearby_ref_lon, float(p_lat), float(p_lon))
                    if calc_dist <= 5.0:
                        if abs(round(calc_dist, 2) - item.get("distance_km", 0.0)) > 0.05:
                            item["distance_km"] = round(calc_dist, 2)
                        formatted_nearby.append(item)
        else:
            nearby_provenance = nearby_prov
            formatted_nearby = []
        raw_routes = route_result.get("routes")
        if isinstance(raw_routes, dict):
            opt = raw_routes
        elif isinstance(raw_routes, list):
            opt = {
                "recommended_route": raw_routes[0] if raw_routes else None,
                "route_options": raw_routes
            }
        else:
            opt = {}

        # Synchronize provider statuses from router and final route options
        final_provider_statuses = dict(route_result.get("provider_statuses", {}))
        
        # Check if road route exists in route_options or journeys
        has_road = any(
            r.get("provider") == "OSRM" or (r.get("mode") or "").lower() in ("driving", "road")
            for r in (all_route_options + journeys_list)
        )
        if has_road:
            final_provider_statuses["OSRM"] = "Route calculated"
        elif "OSRM" not in final_provider_statuses:
            final_provider_statuses["OSRM"] = "No itinerary found"

        # Check if verified train routes exist
        has_trains = any(
            r.get("provider") in ("Indian Railways Timetable", "IndianRailways-ScheduleVerified", "RailRadar")
            or (r.get("mode") or "").lower() in ("rail", "train")
            for r in (all_route_options + journeys_list)
        )
        if has_trains:
            final_provider_statuses["Indian Railways Timetable"] = "Connected"
        elif "Indian Railways Timetable" not in final_provider_statuses:
            final_provider_statuses["Indian Railways Timetable"] = "No itinerary found"

        # RailRadar rate limit / quota check
        rr_audit_check = provider_audit.get("RailRadar", {})
        if rr_audit_check.get("status") in ("QUOTA_EXHAUSTED", "RATE_LIMITED") or "quota" in str(rr_audit_check.get("reason", "")).lower() or "rate limit" in str(rr_audit_check.get("reason", "")).lower():
            if "quota" in str(rr_audit_check.get("reason", "")).lower() or rr_audit_check.get("status") == "QUOTA_EXHAUSTED":
                final_provider_statuses["RailRadar"] = "Monthly quota exhausted"
            else:
                final_provider_statuses["RailRadar"] = "Rate limited"

        # Transitous status check
        has_transitous = any(
            r.get("provider") == "Transitous" or "transitous" in str(r.get("route_id", "")).lower()
            for r in (all_route_options + journeys_list)
        )
        if has_transitous:
            final_provider_statuses["Transitous"] = "Connected"
        elif "Transitous" not in final_provider_statuses:
            final_provider_statuses["Transitous"] = "No itinerary found"

        # FlightProvider status check
        has_flights = any(
            r.get("provider") == "FlightProvider" or (r.get("mode") or "").lower() in ("flight", "commercial flight")
            for r in (all_route_options + journeys_list)
        )
        if has_flights:
            final_provider_statuses["FlightProvider"] = "Connected"
        elif "FlightProvider" not in final_provider_statuses or final_provider_statuses.get("FlightProvider") in ("No itinerary found", "Unavailable"):
            fl_audit_check = provider_audit.get("FlightProvider", {})
            if "subscription" in str(fl_audit_check.get("reason", "")).lower() or "subscription" in str(fl_audit_check.get("category", "")).lower():
                final_provider_statuses["FlightProvider"] = "Subscription restricted"

        # ── Straight-line Distance Calculation ───────────────────────────
        straight_dist = round(haversine_distance(geo_orig["lat"], geo_orig["lon"], geo_dest["lat"], geo_dest["lon"]), 1) if (geo_orig and geo_orig.get("lat") is not None and geo_dest.get("lat") is not None) else 0.0

        # ── Category A: AI Transit Strategy ─────────────────────────────
        ai_strategy = route_result.get("route_guidance")
        if not ai_strategy:
            from .ai_route_guidance import AIRouteGuidanceService
            ai_strategy = AIRouteGuidanceService.generate_strategy(
                origin_name=orig_short,
                dest_name=dest_short,
                journey_scale=scale,
                origin_country=geo_orig.get("country_code", "") if geo_orig else "",
                dest_country=geo_dest.get("country_code", "") if geo_dest else "",
                distance_km=straight_dist,
                search_id=req_id,
            )

        # ── Category B: Verified Journey Results ─────────────────────────
        verified_routes_list = [r for r in all_route_options if r.get("provider") and r.get("provider") != "Estimated"]
        has_verified_itins = bool(verified_routes_list and is_verified)

        rec_m = (ai_strategy.get("recommended_mode") or "").lower() if ai_strategy else ""
        if has_verified_itins:
            v_status = "VERIFIED_ITINERARIES_AVAILABLE"
            v_msg = f"{len(verified_routes_list)} verified itinerary available." if len(verified_routes_list) == 1 else f"{len(verified_routes_list)} verified itineraries available."
            v_level = "PROVIDER_VERIFIED"
        else:
            v_status = "NO_VERIFIED_ITINERARY"
            if "flight" in rec_m:
                v_msg = "No verified flight itinerary available for selected date."
            elif "rail" in rec_m or "train" in rec_m:
                v_msg = "No verified train itinerary available for selected date."
            else:
                v_msg = "No verified transit itinerary available for selected date."
            v_level = "UNVERIFIED"

        verified_journey_results = {
            "category": "VERIFIED_JOURNEY_RESULTS",
            "status": v_status,
            "has_verified_itineraries": has_verified_itins,
            "count": len(verified_routes_list) if has_verified_itins else 0,
            "message": v_msg,
            "itineraries": verified_routes_list if has_verified_itins else [],
            "provider_statuses": final_provider_statuses,
            "verification_level": v_level,
        }

        # ── Category C: External Travel Research ─────────────────────────
        from .external_travel_research import ExternalTravelResearchService
        external_research = ExternalTravelResearchService.get_research(
            origin_name=origin,
            dest_name=destination,
            origin_lat=geo_orig["lat"] if geo_orig else None,
            origin_lon=geo_orig["lon"] if geo_orig else None,
            dest_lat=geo_dest["lat"] if geo_dest else None,
            dest_lon=geo_dest["lon"] if geo_dest else None,
            distance_km=straight_dist,
            scale=scale,
            origin_country=geo_orig.get("country_code", "") if geo_orig else "",
            dest_country=geo_dest.get("country_code", "") if geo_dest else "",
        )

        # Base response payload
        base_response = {
            "request_id": req_id,
            "status": status,
            "result_level": result_level,
            "verified": has_verified_itins,
            "journey_scale": scale,
            "origin": orig_short,
            "destination": dest_short,
            "requested_origin": origin,
            "requested_destination": destination,
            "origin_source": resolved_origin_source,
            "origin_accuracy_m": acc,
            "origin_coords": {"lat": geo_orig["lat"] if geo_orig else None, "lon": geo_orig["lon"] if geo_orig else None, "accuracy": acc},
            "dest_coords": {"lat": geo_dest["lat"], "lon": geo_dest["lon"]},
            "search_origin_coords": {"lat": geo_orig["lat"] if geo_orig else None, "lon": geo_orig["lon"] if geo_orig else None},
            "search_dest_coords": {"lat": geo_dest["lat"], "lon": geo_dest["lon"]},
            "preferred_mode": preferred_mode,
            
            # The Three Distinct Information Categories
            "ai_transit_strategy": ai_strategy,
            "verified_journey_results": verified_journey_results,
            "external_travel_research": external_research,

            # Route Optimization Schema — all strategies
            "recommended_route": opt.get("recommended_route"),
            "route_options": opt.get("route_options", []),
            "journeys": route_result.get("journeys", []),
            "fastest_route": opt.get("fastest_route"),
            "cheapest_route": opt.get("cheapest_route"),
            "least_walking_route": opt.get("least_walking_route"),
            "safest_route": opt.get("safest_route"),
            "greenest_route": opt.get("greenest_route"),
            "fewest_transfers_route": opt.get("fewest_transfers_route"),
            "best_overall_route": opt.get("best_overall_route"),
            "optimization": opt.get("optimization", {}),
            
            "provider_trace": route_result.get("provider_trace", []),
            "provider_audit": route_result.get("provider_audit", {}),
            "provider_statuses": final_provider_statuses,
            "route_guidance": ai_strategy,
            "why_this_route": why_this_route,
            "message": v_msg if not has_verified_itins else route_result.get("message"),
            "nearby": formatted_nearby,
            "nearby_provenance": nearby_provenance,
            "weather_obj": {
                "stops": [
                    {"location": orig_short, "temp": f"{weather_orig['temp_c']}°C" if geo_orig else "N/A", "icon": weather_orig.get("icon", "☀️") if geo_orig else "☀️"},
                    {"location": dest_short, "temp": f"{weather_dest['temp_c']}°C", "icon": weather_dest.get("icon", "☀️")},
                ]
            },
            "discovered_infrastructure": {
                "nearby_stations": formatted_nearby[:6],
            },
            "nearby_places": nearby_places,
            "live_tracking": LiveTransitService.get_live_tracking(
                origin_lat=geo_orig["lat"] if geo_orig else None,
                origin_lon=geo_orig["lon"] if geo_orig else None,
                dest_lat=geo_dest["lat"] if geo_dest else None,
                dest_lon=geo_dest["lon"] if geo_dest else None,
                routes=all_route_options,
            ),
            "departure_plan": {
                "requested_departure": req_dep_dt.isoformat(),
                "requested_departure_display": req_dep_dt.strftime("%I:%M %p").lstrip("0"),
                "departure_type": dep_type_clean,
                "date": str(planning_date),
                "timezone": tz_name,
                "boarding_buffer_min": int(os.getenv("TRANSIT_BOARDING_BUFFER_MINUTES", "5")),
                "transfer_buffer_min": int(os.getenv("TRANSIT_TRANSFER_BUFFER_MINUTES", "5")),
            },
        }

        return base_response


def _normalize_journey_model(
    route_result: Dict[str, Any],
    geo_orig: Optional[Dict[str, Any]],
    geo_dest: Dict[str, Any],
    orig_short: str,
    dest_short: str,
    infra_res: Dict[str, Any],
    is_verified: bool,
    scale: str,
) -> Dict[str, Any]:
    status = route_result.get("status", "ROUTING_UNAVAILABLE")
    road_alt = route_result.get("road_alternative")
    journey = route_result.get("journey") or {}

    orig_lat = geo_orig["lat"] if geo_orig else 0.0
    orig_lon = geo_orig["lon"] if geo_orig else 0.0
    dest_lat = geo_dest["lat"]
    dest_lon = geo_dest["lon"]
    straight_line_dist = round(haversine_distance(orig_lat, orig_lon, dest_lat, dest_lon), 1)

    # 1. Distance & Duration Summaries
    if status == "SAME_LOCATION":
        dist_summary = {
            "total_distance_km": straight_line_dist,
            "distance_type": "WALKING",
            "source": "Haversine Distance (<0.5 km)",
            "status": "VERIFIED",
        }
        walk_mins = max(1.0, round(straight_line_dist * 15.0, 1))
        dur_summary = {
            "total_duration_min": walk_mins,
            "source": "Derived Walking Speed",
            "status": "ESTIMATED",
        }
        segments = [
            {
                "mode": "Walking",
                "from": orig_short,
                "to": dest_short,
                "distance_km": straight_line_dist,
                "duration_min": walk_mins,
                "status": "VERIFIED",
                "source": "Haversine Distance",
                "confidence": "HIGH",
            }
        ]
        timeline = [
            {"time": "Start", "title": orig_short, "description": "Origin location", "status": "VERIFIED", "type": "ORIGIN"},
            {"time": f"{walk_mins} min", "title": f"🚶 Walking · {orig_short} → {dest_short}", "description": f"{straight_line_dist} km walking distance (< 500m)", "status": "VERIFIED", "mode": "Walking", "source": "Haversine", "distance_km": straight_line_dist, "duration_min": walk_mins, "type": "SEGMENT"},
            {"time": "Arrival", "title": dest_short, "description": "Destination reached", "status": "VERIFIED", "type": "DESTINATION"},
        ]

    elif status == "VERIFIED_ROAD_ALTERNATIVE" and road_alt:
        road_dist = road_alt.get("distance_km", straight_line_dist)
        road_dur = road_alt.get("duration_min") or road_alt.get("duration_minutes") or round(road_dist * 1.2, 1)
        dist_summary = {
            "total_distance_km": road_dist,
            "distance_type": "ROAD",
            "source": "OSRM",
            "status": "VERIFIED",
        }
        dur_summary = {
            "total_duration_min": road_dur,
            "source": "OSRM",
            "status": "VERIFIED",
        }
        segments = [
            {
                "mode": "Driving",
                "from": orig_short,
                "to": dest_short,
                "distance_km": road_dist,
                "duration_min": road_dur,
                "status": "VERIFIED",
                "source": "OSRM",
                "confidence": "HIGH",
            }
        ]
        dur_str = f"{int(road_dur // 60)}h {int(road_dur % 60)}m" if road_dur >= 60 else f"{int(road_dur)}m"
        timeline = [
            {"time": "Departure", "title": orig_short, "description": "Journey starts from origin", "status": "VERIFIED", "type": "ORIGIN"},
            {"time": dur_str, "title": f"🚗 Driving · {orig_short} → {dest_short}", "description": f"{road_dist} km via OSRM verified road network", "status": "VERIFIED", "mode": "Driving", "source": "OSRM", "distance_km": road_dist, "duration_min": road_dur, "type": "SEGMENT"},
            {"time": "Arrival", "title": dest_short, "description": "Journey completed at destination", "status": "VERIFIED", "type": "DESTINATION"},
        ]

    elif status == "VERIFIED_FLIGHT" and journey.get("itineraries"):
        fl = journey["itineraries"][0]
        orig_ap = fl.get("origin_airport") or "Origin Airport"
        dest_ap = fl.get("destination_airport") or "Destination Airport"
        fl_num = fl.get("flight_number") or "Verified Flight"
        
        # In-air flight metrics vs door-to-door metrics
        in_air_dist = fl.get("flight_distance_km") or fl.get("distance_km") or straight_line_dist
        in_air_dur = fl.get("flight_duration_minutes") or 120.0

        # Total door-to-door metrics
        total_flight_dist = fl.get("total_distance_km") or fl.get("distance_km") or in_air_dist
        total_flight_dur = fl.get("total_duration_minutes") or fl.get("duration_minutes") or in_air_dur

        orig_transfer_km = round(haversine_distance(geo_orig["lat"], geo_orig["lon"], fl.get("origin_lat", geo_orig["lat"]), fl.get("origin_lon", geo_orig["lon"])), 1)
        orig_transfer_min = max(10, round(orig_transfer_km * 1.5, 1))
        
        dest_transfer_km = round(haversine_distance(fl.get("destination_lat", geo_dest["lat"]), fl.get("destination_lon", geo_dest["lon"]), geo_dest["lat"], geo_dest["lon"]), 1)
        dest_transfer_min = max(10, round(dest_transfer_km * 1.5, 1))

        orig_ap_label = orig_ap if "airport" in orig_ap.lower() else f"{orig_ap} Airport"
        dest_ap_label = dest_ap if "airport" in dest_ap.lower() else f"{dest_ap} Airport"

        dist_summary = {
            "total_distance_km": total_flight_dist,
            "flight_distance_km": in_air_dist,
            "distance_type": "MULTIMODAL_AIR",
            "source": "FlightProvider (AviationStack) + OSRM Ground",
            "status": "VERIFIED",
        }
        dur_summary = {
            "total_duration_min": total_flight_dur,
            "flight_duration_min": in_air_dur,
            "source": "FlightProvider (AviationStack) + OSRM Ground",
            "status": "VERIFIED",
        }
        segments = [
            {
                "mode": "Transfer",
                "from": orig_short,
                "to": orig_ap_label,
                "distance_km": orig_transfer_km,
                "duration_min": orig_transfer_min,
                "status": "ESTIMATED",
                "source": "DERIVED",
                "confidence": "MEDIUM",
            },
            {
                "mode": "Flight",
                "from": orig_ap_label,
                "to": dest_ap_label,
                "distance_km": in_air_dist,
                "duration_min": in_air_dur,
                "status": "VERIFIED",
                "source": "FlightProvider",
                "confidence": "HIGH",
                "flight_number": fl_num,
                "airline": fl.get("airline") or fl.get("airline_name"),
            },
            {
                "mode": "Transfer",
                "from": dest_ap_label,
                "to": dest_short,
                "distance_km": dest_transfer_km,
                "duration_min": dest_transfer_min,
                "status": "ESTIMATED",
                "source": "DERIVED",
                "confidence": "MEDIUM",
            },
        ]
        fl_h = int(in_air_dur // 60)
        fl_m = int(round(in_air_dur % 60))
        fl_dur_str = f"{fl_h}h {fl_m}m" if fl_h > 0 else f"{fl_m} min"

        timeline = [
            {"time": "Sequence 1", "title": orig_short, "description": "Origin location", "status": "VERIFIED", "type": "ORIGIN"},
            {"time": f"{int(orig_transfer_min)} min", "title": f"🚘 Airport Transfer · {orig_short} → {orig_ap_label}", "description": "Ground transfer to departure airport", "status": "ESTIMATED", "mode": "Transfer", "source": "DERIVED", "distance_km": orig_transfer_km, "duration_min": orig_transfer_min, "type": "SEGMENT"},
            {"time": fl_dur_str, "title": f"✈️ Verified Flight ({fl_num}) · {orig_ap_label} → {dest_ap_label}", "description": f"{in_air_dist} km flight via {fl.get('airline') or fl.get('airline_name') or 'FlightProvider'}", "status": "VERIFIED", "mode": "Flight", "source": "FlightProvider", "distance_km": in_air_dist, "duration_min": in_air_dur, "type": "SEGMENT"},
            {"time": f"{int(dest_transfer_min)} min", "title": f"🚘 City Transfer · {dest_ap_label} → {dest_short}", "description": "Ground transfer to final destination", "status": "ESTIMATED", "mode": "Transfer", "source": "DERIVED", "distance_km": dest_transfer_km, "duration_min": dest_transfer_min, "type": "SEGMENT"},
            {"time": "Arrival", "title": dest_short, "description": "Destination reached", "status": "VERIFIED", "type": "DESTINATION"},
        ]

    elif status == "PUBLIC_TRANSIT_AVAILABLE" and journey.get("legs"):
        legs = journey.get("legs", [])
        provider_name = journey.get("provider", "RailRadar")
        tot_dist = journey.get("distance_km", straight_line_dist)
        
        # Exact Duration Calculation
        tot_dur = journey.get("duration_minutes", 120.0)
        dur_source = f"{provider_name} — provider reported"
        dur_method = "provider_reported"
        
        if legs:
            first_leg = legs[0]
            last_leg = legs[-1]
            dep_time_str = first_leg.get("departure_time")
            arr_time_str = last_leg.get("arrival_time")
            
            if dep_time_str and arr_time_str:
                from datetime import datetime
                try:
                    d_str = dep_time_str.replace("Z", "+00:00")
                    a_str = arr_time_str.replace("Z", "+00:00")
                    dep_dt = datetime.fromisoformat(d_str)
                    arr_dt = datetime.fromisoformat(a_str)
                    
                    if dep_dt.tzinfo is not None and arr_dt.tzinfo is None:
                        arr_dt = arr_dt.replace(tzinfo=dep_dt.tzinfo)
                    elif dep_dt.tzinfo is None and arr_dt.tzinfo is not None:
                        dep_dt = dep_dt.replace(tzinfo=arr_dt.tzinfo)
                    
                    if arr_dt <= dep_dt:
                        from datetime import timedelta
                        arr_dt += timedelta(days=1)

                    dur_mins = (arr_dt - dep_dt).total_seconds() / 60.0
                    if dur_mins > 0:
                        tot_dur = dur_mins
                        dur_source = f"{provider_name} (Calculated from timestamps)"
                        dur_method = "first_departure_to_final_arrival"
                        logger.info(f"[TRANSIT][DURATION] provider={provider_name} initial_departure={dep_time_str} final_arrival={arr_time_str} calculated_duration_min={tot_dur} source=timestamp_calculated")
                except Exception as e:
                    logger.error(f"[TRANSIT][DURATION] Failed to parse timestamps: {e}")
                    pass

        dist_summary = {
            "total_distance_km": tot_dist,
            "distance_type": "RAIL",
            "source": provider_name,
            "status": "VERIFIED",
        }
        dur_summary = {
            "total_duration_min": tot_dur,
            "source": dur_source,
            "method": dur_method,
            "status": "VERIFIED",
            "verified": True
        }
        segments = []
        timeline = [{"time": "Departure", "title": orig_short, "description": "Journey starts from origin", "status": "VERIFIED", "type": "ORIGIN"}]
        for idx, leg in enumerate(legs):
            leg_mode = normalize_mode_name(leg.get("mode") or leg.get("type") or "Rail")
            leg_from = normalize_station_name(leg.get("boarding_stop", {}).get("name") or leg.get("from_name") or orig_short)
            leg_to = normalize_station_name(leg.get("alighting_stop", {}).get("name") or leg.get("to_name") or dest_short)
            leg_dist = leg.get("distance_km") or round((leg.get("distance_m", 0) or 0) / 1000.0, 1)
            leg_dur = leg.get("duration_minutes") or leg.get("duration_min")
            if leg_dur is not None:
                try:
                    leg_dur = max(0.0, float(leg_dur))
                except (ValueError, TypeError):
                    pass

            icon = get_mode_icon(leg_mode)
            segments.append({
                "mode": leg_mode.title(),
                "from": leg_from,
                "to": leg_to,
                "distance_km": leg_dist,
                "duration_min": leg_dur,
                "status": "VERIFIED",
                "source": provider_name,
                "confidence": "HIGH",
                "train_number": leg.get("train_number"),
                "train_name": leg.get("train_name"),
                "departure_time": leg.get("departure_time"),
                "arrival_time": leg.get("arrival_time"),
                "platform": leg.get("platform"),
            })
            timeline.append({
                "time": leg.get("departure_time") or f"Leg {idx+1}",
                "title": f"{icon} {leg_mode.title()} · {leg_from} → {leg_to}",
                "description": f"{leg_dist} km via {provider_name}",
                "status": "VERIFIED",
                "mode": leg_mode.title(),
                "source": provider_name,
                "distance_km": leg_dist,
                "duration_min": leg_dur,
                "type": "SEGMENT",
            })
        timeline.append({"time": "Arrival", "title": dest_short, "description": "Journey completed at destination", "status": "VERIFIED", "type": "DESTINATION"})

    elif road_alt:
        road_dist = road_alt.get("distance_km", straight_line_dist)
        road_dur = road_alt.get("duration_min") or road_alt.get("duration_minutes")
        dist_summary = {
            "total_distance_km": road_dist,
            "distance_type": "ROAD_FALLBACK",
            "source": "OSRM Long-Distance",
            "status": "ESTIMATED",
        }
        dur_summary = {
            "total_duration_min": road_dur,
            "source": "OSRM Long-Distance",
            "status": "ESTIMATED",
        }
        segments = [
            {
                "mode": "Driving",
                "from": orig_short,
                "to": dest_short,
                "distance_km": road_dist,
                "duration_min": road_dur,
                "status": "ESTIMATED",
                "source": "OSRM Long-Distance Fallback",
                "confidence": "MEDIUM",
            }
        ]
        dur_str = f"{int(road_dur // 60)}h {int(road_dur % 60)}m" if road_dur and road_dur >= 60 else f"{int(road_dur or 0)}m"
        timeline = [
            {"time": "Departure", "title": orig_short, "description": "Journey starts from origin", "status": "ESTIMATED", "type": "ORIGIN"},
            {"time": dur_str, "title": f"🚗 Driving (Fallback) · {orig_short} → {dest_short}", "description": f"{road_dist} km long-distance road route via OSRM", "status": "ESTIMATED", "mode": "Driving", "source": "OSRM", "distance_km": road_dist, "duration_min": road_dur, "type": "SEGMENT"},
            {"time": "Arrival", "title": dest_short, "description": "Journey completed at destination", "status": "ESTIMATED", "type": "DESTINATION"},
        ]

    else:
        dist_summary = {
            "total_distance_km": straight_line_dist,
            "distance_type": "STRAIGHT_LINE",
            "source": "Haversine Distance",
            "status": "ESTIMATED",
        }
        dur_summary = {
            "total_duration_min": None,
            "source": "Unavailable",
            "status": "UNAVAILABLE",
        }
        segments = [
            {
                "mode": "Travel Guidance",
                "from": orig_short,
                "to": dest_short,
                "distance_km": straight_line_dist,
                "duration_min": None,
                "status": "UNAVAILABLE",
                "source": "Derived Coordinates",
                "confidence": "LOW",
            }
        ]

        if scale in ["INTERCONTINENTAL", "INTERNATIONAL"] or straight_line_dist > 1000:
            timeline = [
                {"time": "1", "title": f"🏠 {orig_short}", "description": "Origin location", "status": "ESTIMATED", "type": "ORIGIN"},
                {"time": "2", "title": f"🌐 Travel Guidance · {orig_short} → {dest_short}", "description": "Consider air travel for this long-distance journey. No verified FlightProvider or RailRadar itinerary is currently available.", "status": "ESTIMATED", "mode": "Travel Guidance", "source": "AI Guidance", "distance_km": straight_line_dist, "duration_min": None, "type": "SEGMENT"},
                {"time": "3", "title": f"📍 {dest_short}", "description": "Destination location", "status": "ESTIMATED", "type": "DESTINATION"},
            ]
        else:
            timeline = [
                {"time": "1", "title": f"🏠 {orig_short}", "description": "Origin location", "status": "ESTIMATED", "type": "ORIGIN"},
                {"time": "2", "title": f"🌐 Travel Guidance · {orig_short} → {dest_short}", "description": "Consider rail or road travel for this route. No verified FlightProvider or RailRadar itinerary is currently available.", "status": "ESTIMATED", "mode": "Travel Guidance", "source": "AI Guidance", "distance_km": straight_line_dist, "duration_min": None, "type": "SEGMENT"},
                {"time": "3", "title": f"📍 {dest_short}", "description": "Destination location", "status": "ESTIMATED", "type": "DESTINATION"},
            ]

    # 2. Route Options — expose ALL verified trains from optimizer
    route_opts = []
    # Rail trains: use all railway options from optimizer
    rail_routes = [r for r in all_route_options if r.get("provider") in ("RailRadar", "Indian Railways Timetable", "IndianRailways-ScheduleVerified") or (r.get("mode") or "").lower() in ("train", "rail")]
    if status == "PUBLIC_TRANSIT_AVAILABLE" and rail_routes:
        for rr in rail_routes:
            p_label = rr.get("provider", "Indian Railways Timetable")
            route_opts.append({
                "route_id": rr.get("route_id"),
                "provider": p_label,
                "mode": rr.get("mode", "Rail"),
                "status": "VERIFIED",
                "distance_km": rr.get("distance_km"),
                "duration_min": rr.get("duration_min"),
                "departure_time": rr.get("departure_time"),
                "arrival_time": rr.get("arrival_time"),
                "departure_time_display": rr.get("departure_time_display"),
                "arrival_time_display": rr.get("arrival_time_display"),
                "is_overnight": rr.get("is_overnight", False),
                "train_number": rr.get("train_number"),
                "train_name": rr.get("train_name"),
                "departure_station": rr.get("departure_station"),
                "arrival_station": rr.get("arrival_station"),
                "operating_days": rr.get("operating_days", []),
                "fare": rr.get("fare"),
                "verification_status": rr.get("verification_status", "SCHEDULE_VERIFIED"),
                "intermediate_stops": rr.get("intermediate_stops", []),
                "geometry": rr.get("geometry", []),
                "legs": rr.get("legs", []),
                "message": f"Train {rr.get('train_number')} — {rr.get('train_name', 'Verified Rail Route')}",
            })
    else:
        route_opts.append({
            "provider": "Indian Railways Timetable",
            "mode": "Rail",
            "status": "UNAVAILABLE",
            "message": "No verified railway itinerary available",
        })

    # Flight Option
    if status == "VERIFIED_FLIGHT" and journey.get("itineraries"):
        fl_num = journey["itineraries"][0].get("flight_number") or "Verified Flight"
        route_opts.append({
            "provider": "FlightProvider",
            "mode": "Flight",
            "status": "VERIFIED",
            "distance_km": dist_summary["total_distance_km"],
            "duration_min": dur_summary["total_duration_min"],
            "message": f"Verified flight option ({fl_num})",
        })
    else:
        route_opts.append({
            "provider": "FlightProvider",
            "mode": "Flight",
            "status": "UNAVAILABLE",
            "message": "No verified flight options available",
        })

    # Road Driving Option
    if status == "VERIFIED_ROAD_ALTERNATIVE" and road_alt:
        route_opts.append({
            "route_id": road_alt.get("route_id") or "osrm_road_route",
            "provider": "OSRM",
            "mode": "Driving",
            "status": "VERIFIED",
            "distance_km": road_alt.get("distance_km"),
            "duration_min": road_alt.get("duration_min") or road_alt.get("duration_minutes"),
            "geometry": road_alt.get("geometry", []),
            "message": f"Verified road route ({road_alt.get('distance_km')} km)",
        })
    elif road_alt:
        route_opts.append({
            "route_id": road_alt.get("route_id") or "osrm_road_route",
            "provider": "OSRM",
            "mode": "Driving",
            "status": "ESTIMATED",
            "distance_km": road_alt.get("distance_km"),
            "duration_min": road_alt.get("duration_min") or road_alt.get("duration_minutes"),
            "geometry": road_alt.get("geometry", []),
            "message": f"Long-distance road fallback ({road_alt.get('distance_km')} km)",
        })
    else:
        route_opts.append({
            "provider": "OSRM",
            "mode": "Driving",
            "status": "UNAVAILABLE",
            "message": "Road route unavailable",
        })

    # 3. Provider Diagnostics (Exactly 5 configured providers)
    nb_count = len(infra_res.get("items", [])) if infra_res else 0
    nearby_prov = infra_res.get("provenance", {}) if infra_res else {}
    fallback_used = nearby_prov.get("fallback_used", False)

    overpass_status = "VERIFIED" if nb_count > 0 and not fallback_used else ("FALLBACK_USED" if nb_count > 0 and fallback_used else "UNAVAILABLE")
    overpass_msg = "Live OpenStreetMap via Overpass API" if overpass_status == "VERIFIED" else ("Live query unavailable; verified geographic fallback used" if overpass_status == "FALLBACK_USED" else "No verified nearby POIs available")

    # Extract detailed diagnostic from provider_audit if available
    fl_audit = provider_audit.get("FlightProvider", {})
    fl_reason = fl_audit.get("reason") or ("Verified flight options returned" if status == "VERIFIED_FLIGHT" else "No verified flight returned")
    fl_status = fl_audit.get("status") or ("SUCCESS" if status == "VERIFIED_FLIGHT" else "NO_RESULT")

    has_train_itins = bool(rail_routes and any(r.get("status") == "VERIFIED" for r in rail_routes))
    rr_audit = provider_audit.get("RailRadar", {})
    rr_audit_status = rr_audit.get("status") or ("RATE_LIMITED" if "429" in str(rr_audit.get("reason", "")) else "UNAVAILABLE")

    provider_diagnostics = [
        {"provider": "Indian Railways Timetable", "configured": True, "status": "VERIFIED" if has_train_itins else "NO_ITINERARY", "message": f"Verified IRCTC timetable options ({len(rail_routes)} trains)" if has_train_itins else "No verified timetable records"},
        {"provider": "RailRadar", "configured": True, "status": "VERIFIED" if (journey.get("provider") == "RailRadar" and journey.get("verification_status") == "LIVE_VERIFIED") else rr_audit_status, "message": "Live verified railway API" if (journey.get("provider") == "RailRadar" and journey.get("verification_status") == "LIVE_VERIFIED") else (rr_audit.get("reason") or "RailRadar quota exceeded or rate limited")},
        {"provider": "FlightProvider", "configured": fl_audit.get("configured", True), "status": "VERIFIED" if status == "VERIFIED_FLIGHT" else (fl_audit.get("category") or "UNAVAILABLE"), "message": fl_reason},
        {"provider": "OSRM", "configured": True, "status": "VERIFIED" if status == "VERIFIED_ROAD_ALTERNATIVE" else ("ESTIMATED" if road_alt else "UNAVAILABLE"), "message": f"Verified road route: {road_alt.get('distance_km')} km" if status == "VERIFIED_ROAD_ALTERNATIVE" and road_alt else (f"Long-distance road fallback: {road_alt.get('distance_km')} km" if road_alt else "Road route unavailable")},
        {"provider": "Overpass", "configured": True, "status": overpass_status, "message": overpass_msg},
        {"provider": "Nominatim", "configured": True, "status": "VERIFIED", "message": "Origin/destination geocoded"},
    ]

    # Clean provider_audit to contain ONLY configured providers
    clean_audit = {
        "Indian Railways Timetable": {"configured": True, "attempted": True, "status": "SUCCESS" if has_train_itins else "NO_ITINERARY", "reason": f"Verified rail schedules available ({len(rail_routes)} trains)" if has_train_itins else "No verified timetable records"},
        "RailRadar": {"configured": True, "attempted": True, "status": "SUCCESS" if (journey.get("provider") == "RailRadar" and journey.get("verification_status") == "LIVE_VERIFIED") else ("QUOTA_EXHAUSTED" if "quota" in str(rr_audit.get("reason", "")).lower() else "RATE_LIMITED"), "reason": rr_audit.get("reason") or "RailRadar monthly quota reached (HTTP 429)"},
        "FlightProvider": {
            "configured": fl_audit.get("configured", True),
            "attempted": True,
            "status": fl_status,
            "category": fl_audit.get("category"),
            "http_status": fl_audit.get("http_status"),
            "reason": fl_reason,
        },
        "OSRM": {"configured": True, "attempted": True, "status": "SUCCESS" if road_alt else "NO_RESULT", "reason": f"Verified road route ({road_alt.get('distance_km')} km)" if road_alt else "No road route returned"},
        "Overpass": {"configured": True, "attempted": True, "status": "SUCCESS" if nb_count > 0 else "NO_RESULT", "reason": overpass_msg},
        "Nominatim": {"configured": True, "attempted": True, "status": "SUCCESS", "reason": "Origin and destination geocoded successfully"},
    }

    # 4. Strategy Analysis (TASK 10)
    fastest_opt = min([o for o in route_opts if o.get("status") == "VERIFIED" and o.get("duration_min")], key=lambda x: x["duration_min"], default=None)
    
    if fastest_opt:
        fastest_rec = f"{fastest_opt['mode']} via {fastest_opt['provider']} ({fastest_opt['duration_min']} min)"
        best_rec = f"{fastest_opt['mode']} via {fastest_opt['provider']}"
        strategy_analysis = {
            "fastest": {
                "title": "Fastest Route",
                "recommendation": fastest_rec,
                "status": "VERIFIED",
                "note": ""
            },
            "cheapest": {
                "title": "Cheapest Option",
                "recommendation": "N/A",
                "status": "INSUFFICIENT_DATA",
                "note": "No verified fare data.",
            },
            "safest": {
                "title": "Safest Transportation",
                "recommendation": "N/A",
                "status": "INSUFFICIENT_DATA",
                "note": "No verified safety data."
            },
            "greenest": {
                "title": "Lowest CO2 Impact",
                "recommendation": "N/A",
                "status": "INSUFFICIENT_DATA",
                "note": "No verified emissions data."
            },
            "least_walking": {
                "title": "Least Walking",
                "recommendation": "Exact walking distance unavailable.",
                "status": "INSUFFICIENT_DATA",
                "note": "Walking distances not fully verified."
            },
            "best_overall": {
                "title": "Best Overall",
                "recommendation": best_rec,
                "status": "VERIFIED",
                "note": ""
            },
        }
    else:
        is_flight = scale in ["INTERCONTINENTAL", "INTERNATIONAL"] or straight_line_dist > 1000
        best_rec = "Air travel is the practical high-level option, but no verified itinerary is available." if is_flight else "Rail or road travel is the practical high-level option, but no verified itinerary is available."
        strategy_analysis = {
            "fastest": {
                "title": "Fastest Route",
                "recommendation": "Insufficient verified data",
                "status": "UNAVAILABLE",
                "note": ""
            },
            "cheapest": {
                "title": "Cheapest Option",
                "recommendation": "Insufficient verified fare data",
                "status": "UNAVAILABLE",
                "note": ""
            },
            "safest": {
                "title": "Safest Transportation",
                "recommendation": "No verified comparison available",
                "status": "UNAVAILABLE",
                "note": ""
            },
            "greenest": {
                "title": "Lowest CO2 Impact",
                "recommendation": "No verified multimodal comparison available",
                "status": "UNAVAILABLE",
                "note": ""
            },
            "least_walking": {
                "title": "Least Walking",
                "recommendation": "No verified walking comparison available",
                "status": "UNAVAILABLE",
                "note": ""
            },
            "best_overall": {
                "title": "Best Overall",
                "recommendation": best_rec,
                "status": "ESTIMATED",
                "note": ""
            },
        }

    return {
        "distance_summary": dist_summary,
        "duration_summary": dur_summary,
        "journey_segments": segments,
        "journey_timeline": timeline,
        "route_options": route_opts,
        "all_route_options": all_route_options,  # Full list from optimizer (all 7 trains + OSRM)
        "journeys": journeys_list,
        "recommended_route": journey,
        "provider_diagnostics": provider_diagnostics,
        "provider_audit": clean_audit,
        "provider_statuses": route_result.get("provider_statuses", {}),
        "message": route_result.get("message"),
        "strategy_analysis": strategy_analysis,
        "status": status,
    }
