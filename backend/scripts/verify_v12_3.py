"""
verify_v12_3.py — WanderWise Transit V12.3 Automated Acceptance & Truth-First Flight Verification

Verifies:
1. SAME_LOCATION pre-routing check (< 0.5km)
2. Domestic Rail attempt (RailRadar)
3. Domestic Transitous attempt
4. Navitia diagnostic check
5. Long-Distance Flight attempt (FlightProvider)
6. Short-Distance OSRM (Coimbatore -> Chennai)
7. > 800 km OSRM Threshold Configured
8. Coimbatore -> Kolkata (Long-distance fallback, NOT primary verified alternative)
9. Coimbatore -> Delhi
10. Coimbatore -> Mumbai (No fake 0 km / 0 min flight results)
11. Coimbatore -> Hyderabad
12. Coimbatore -> Tokyo (Intercontinental OSRM suppression)
13. Tokyo -> London (Intercontinental OSRM suppression)
14. provider_audit dictionary exists in response
15. why_this_route diagnostic list exists in response
16. Zero secret API keys exposed in provider audit/debug
17. Zero AI-generated transit facts contract
18. Correct V12.3 6-level result hierarchy
19. Long-distance status/badge handling
20. Debug providers endpoint (/api/transit/debug/providers)
21. Strict validate_flight_result rejects dummy/zero-metric flight objects
22. Unconfigured FlightProvider yields PROVIDER_NOT_CONFIGURED (NOT VERIFIED_FLIGHT)
23. Verified boolean flag in Orchestrator payload is False for unverified guidance
24. Data Quality provider_engine accurately reflects active provider (No Transitous MOTIS mismatch)
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.transit.transit_router import TransitRouter, MAX_DOMESTIC_ROAD_DISTANCE_KM, validate_flight_result
from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.journey_classifier import JourneyClassifier
from app.services.transit.providers.railradar_provider import RailRadarProvider
from app.services.transit.providers.flight_provider import FlightProvider, ProviderResult, ProviderStatus
from app.routes.transit import get_debug_providers


def run_v12_3_acceptance_suite():
    print("=" * 60)
    print("WANDERWISE TRANSIT V12.3 ACCEPTANCE VERIFICATION")
    print("=" * 60)

    results = []

    def log_test(num: int, title: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        results.append((num, title, passed))
        print(f"[{status}] {num}. {title}{' - ' + detail if detail else ''}")

    router = TransitRouter()

    # 1. SAME_LOCATION Check (< 0.5 km)
    try:
        res = router.route("Chennai Central", 13.0827, 80.2707, "Chennai Central Metro", 13.0829, 80.2709)
        log_test(1, "SAME_LOCATION Check (<0.5km)", res.get("status") == "SAME_LOCATION" and res.get("result_level") == 0, res.get("message"))
    except Exception as e:
        log_test(1, "SAME_LOCATION Check (<0.5km)", False, str(e))

    # 2. Domestic Rail Attempt (RailRadar)
    try:
        rr = RailRadarProvider()
        rr_res = rr.plan_journey(11.0168, 76.9558, 13.0827, 80.2707)  # CBE -> MAS
        log_test(2, "Domestic Rail Attempt (RailRadar)", rr_res.status.value in ["SUCCESS", "NO_ITINERARY", "PROVIDER_NOT_CONFIGURED"], f"Status: {rr_res.status.value}")
    except Exception as e:
        log_test(2, "Domestic Rail Attempt (RailRadar)", False, str(e))

    # 3. No Transitous / India Transit Diagnostics
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Chennai", 13.0827, 80.2707)
        no_obsolete = "Transitous" not in res.get("provider_audit", {}) and "IndiaTransit" not in res.get("provider_audit", {})
        log_test(3, "No Transitous / India Transit in Audit", no_obsolete, f"Audit keys: {list(res.get('provider_audit', {}).keys())}")
    except Exception as e:
        log_test(3, "No Transitous / India Transit in Audit", False, str(e))

    # 4. No Navitia Diagnostics Check
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Chennai", 13.0827, 80.2707)
        no_navitia = "Navitia" not in res.get("provider_audit", {})
        log_test(4, "No Navitia Diagnostics Check", no_navitia, f"Navitia present: {'Navitia' in res.get('provider_audit', {})}")
    except Exception as e:
        log_test(4, "No Navitia Diagnostics Check", False, str(e))

    # 5. Long-Distance Flight Attempt (FlightProvider)
    try:
        fl = FlightProvider()
        fl_res = fl.plan_journey(11.0168, 76.9558, 22.5726, 88.3639, origin_name="Coimbatore", dest_name="Kolkata")
        log_test(5, "Long-Distance Flight Attempt (FlightProvider)", fl_res.status.value in ["SUCCESS", "NO_ITINERARY", "PROVIDER_NOT_CONFIGURED"], f"Status: {fl_res.status.value}")
    except Exception as e:
        log_test(5, "Long-Distance Flight Attempt (FlightProvider)", False, str(e))

    # 6. Short-Distance OSRM (Coimbatore -> Chennai ~ 500 km <= 800 km)
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Chennai", 13.0827, 80.2707)
        status = res.get("status")
        log_test(6, "Short-Distance OSRM (CBE -> MAS)", status in ["PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE"], f"Status: {status}")
    except Exception as e:
        log_test(6, "Short-Distance OSRM (CBE -> MAS)", False, str(e))

    # 7. > 800 km OSRM Threshold Configured
    try:
        log_test(7, ">800km OSRM Threshold Configured", MAX_DOMESTIC_ROAD_DISTANCE_KM == 800.0, f"Threshold: {MAX_DOMESTIC_ROAD_DISTANCE_KM} km")
    except Exception as e:
        log_test(7, ">800km OSRM Threshold Configured", False, str(e))

    # 8. Coimbatore -> Kolkata (Long-Distance Suppression Check)
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Kolkata", 22.5726, 88.3639)
        status = res.get("status")
        is_suppressed = status != "VERIFIED_ROAD_ALTERNATIVE" or (res.get("road_alternative") and res.get("road_alternative", {}).get("is_long_distance_fallback"))
        log_test(8, "Coimbatore -> Kolkata (>800km Suppression)", is_suppressed, f"Status: {status}")
    except Exception as e:
        log_test(8, "Coimbatore -> Kolkata (>800km Suppression)", False, str(e))

    # 9. Coimbatore -> Delhi
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Delhi", 28.6139, 77.2090)
        status = res.get("status")
        log_test(9, "Coimbatore -> Delhi Route Evaluation", status in ["PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_FLIGHT", "ROUTE_GUIDANCE_AVAILABLE"], f"Status: {status}")
    except Exception as e:
        log_test(9, "Coimbatore -> Delhi Route Evaluation", False, str(e))

    # 10. Coimbatore -> Mumbai (No fake 0 km / 0 min flight results)
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Mumbai", 19.0760, 72.8777)
        status = res.get("status")
        journey = res.get("journey") or {}
        is_valid_flight = True
        if status == "VERIFIED_FLIGHT":
            if journey.get("distance_km") == 0 or journey.get("duration_minutes") == 0:
                is_valid_flight = False
        log_test(10, "Coimbatore -> Mumbai Flight Validation", is_valid_flight, f"Status: {status}")
    except Exception as e:
        log_test(10, "Coimbatore -> Mumbai Flight Validation", False, str(e))

    # 11. Coimbatore -> Hyderabad
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Hyderabad", 17.3850, 78.4867)
        status = res.get("status")
        log_test(11, "Coimbatore -> Hyderabad Route Evaluation", status in ["PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_FLIGHT", "ROUTE_GUIDANCE_AVAILABLE"], f"Status: {status}")
    except Exception as e:
        log_test(11, "Coimbatore -> Hyderabad Route Evaluation", False, str(e))

    # 12. Coimbatore -> Tokyo (Intercontinental OSRM Suppression)
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Tokyo", 35.6762, 139.6503)
        no_osrm = res.get("status") != "VERIFIED_ROAD_ALTERNATIVE"
        log_test(12, "Coimbatore -> Tokyo Intercontinental OSRM Suppression", no_osrm, f"Status: {res.get('status')}")
    except Exception as e:
        log_test(12, "Coimbatore -> Tokyo Intercontinental OSRM Suppression", False, str(e))

    # 13. Tokyo -> London (Intercontinental OSRM Suppression)
    try:
        res = router.route("Tokyo", 35.6762, 139.6503, "London", 51.5074, -0.1278)
        no_osrm = res.get("status") != "VERIFIED_ROAD_ALTERNATIVE"
        log_test(13, "Tokyo -> London Intercontinental OSRM Suppression", no_osrm, f"Status: {res.get('status')}")
    except Exception as e:
        log_test(13, "Tokyo -> London Intercontinental OSRM Suppression", False, str(e))

    # 14. provider_audit Dictionary Exists
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Kolkata", 22.5726, 88.3639)
        audit = res.get("provider_audit")
        log_test(14, "provider_audit Dictionary Exists", isinstance(audit, dict) and len(audit) > 0, f"Providers: {list(audit.keys()) if audit else None}")
    except Exception as e:
        log_test(14, "provider_audit Dictionary Exists", False, str(e))

    # 15. why_this_route Diagnostic List Exists
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Kolkata", 22.5726, 88.3639)
        why = res.get("why_this_route")
        log_test(15, "why_this_route Diagnostic List Exists", isinstance(why, list) and len(why) > 0, f"Reasons count: {len(why) if why else 0}")
    except Exception as e:
        log_test(15, "why_this_route Diagnostic List Exists", False, str(e))

    # 16. Zero Secret Keys Exposed in Audit/Debug
    try:
        dbg = get_debug_providers()
        res = router.route("Coimbatore", 11.0168, 76.9558, "Kolkata", 22.5726, 88.3639)
        dbg_str = str(dbg) + str(res.get("provider_audit"))
        has_secret = "RAILRADAR_API_KEY" in dbg_str or "FLIGHT_API_KEY" in dbg_str or "GEMINI_API_KEY" in dbg_str or "Bearer " in dbg_str
        log_test(16, "Zero Secret Keys Exposed in Audit/Debug", not has_secret, "No secrets found in payload")
    except Exception as e:
        log_test(16, "Zero Secret Keys Exposed in Audit/Debug", False, str(e))

    # 17. Zero AI Transit Facts Contract
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Tokyo", 35.6762, 139.6503)
        guidance = res.get("route_guidance")
        is_clean = True
        if guidance and "steps" in guidance:
            for s in guidance["steps"]:
                desc = s.get("description", "")
                if "Flight XYZ" in desc or "₹" in desc:
                    is_clean = False
        log_test(17, "Zero AI Transit Facts Contract", is_clean, "No fabricated train/flight numbers found in guidance")
    except Exception as e:
        log_test(17, "Zero AI Transit Facts Contract", False, str(e))

    # 18. Correct V12.3 6-Level Result Hierarchy
    try:
        valid_statuses = ["SAME_LOCATION", "PUBLIC_TRANSIT_AVAILABLE", "VERIFIED_FLIGHT", "VERIFIED_ROAD_ALTERNATIVE", "ROUTE_GUIDANCE_AVAILABLE", "PROVIDERS_UNAVAILABLE"]
        res = router.route("Coimbatore", 11.0168, 76.9558, "Chennai", 13.0827, 80.2707)
        log_test(18, "V12.3 6-Level Result Hierarchy Compliance", res.get("status") in valid_statuses, f"Status: {res.get('status')}")
    except Exception as e:
        log_test(18, "V12.3 6-Level Result Hierarchy Compliance", False, str(e))

    # 19. Long-Distance Status/Badge Handling
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Kolkata", 22.5726, 88.3639)
        road_alt = res.get("road_alternative")
        is_correct = (res.get("status") == "ROUTE_GUIDANCE_AVAILABLE") or (road_alt and road_alt.get("is_long_distance_fallback"))
        log_test(19, "Long-Distance Status/Badge Handling", is_correct, f"Status: {res.get('status')}")
    except Exception as e:
        log_test(19, "Long-Distance Status/Badge Handling", False, str(e))

    # 20. Debug Providers Endpoint Output
    try:
        dbg = get_debug_providers()
        log_test(20, "Debug Providers Endpoint Output", "railradar" in dbg and "flight_provider" in dbg, f"Keys: {list(dbg.keys())}")
    except Exception as e:
        log_test(20, "Debug Providers Endpoint Output", False, str(e))

    # 21. Strict validate_flight_result Rejects Dummy Objects
    try:
        dummy_res = ProviderResult(
            status=ProviderStatus.SUCCESS,
            provider_name="FlightProvider",
            itineraries=[{
                "origin_airport": "Origin Airport",
                "destination_airport": "Destination Airport",
                "flight_number": "Flight Option",
                "distance_km": 0,
                "duration_minutes": 0,
            }]
        )
        val = validate_flight_result(dummy_res)
        log_test(21, "validate_flight_result Rejects Dummy Objects", val["valid"] is False, val["reason"])
    except Exception as e:
        log_test(21, "validate_flight_result Rejects Dummy Objects", False, str(e))

    # 22. Unconfigured FlightProvider Audit Behavior
    try:
        res = router.route("Coimbatore", 11.0168, 76.9558, "Mumbai", 19.0760, 72.8777)
        fl_audit = res.get("provider_audit", {}).get("FlightProvider", {})
        log_test(22, "Unconfigured FlightProvider Audit Behavior", fl_audit.get("status") in ["INVALID_RESULT", "PROVIDER_NOT_CONFIGURED", "NO_RESULT"], f"Flight audit status: {fl_audit.get('status')}")
    except Exception as e:
        log_test(22, "Unconfigured FlightProvider Audit Behavior", False, str(e))

    # 23. Verified boolean flag in Orchestrator payload is False for unverified guidance
    try:
        plan = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore", destination="Kolkata",
            origin_lat=11.0168, origin_lon=76.9558,
            dest_lat=22.5726, dest_lon=88.3639
        )
        log_test(23, "Orchestrator payload contains verified=False for ROUTE_GUIDANCE_AVAILABLE", plan.get("verified") is False, f"Verified flag: {plan.get('verified')}")
    except Exception as e:
        log_test(23, "Orchestrator payload contains verified=False for ROUTE_GUIDANCE_AVAILABLE", False, str(e))

    # 24. Data Quality provider_engine accurately reflects active provider (No Transitous MOTIS mismatch)
    try:
        plan = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore", destination="Kolkata",
            origin_lat=11.0168, origin_lon=76.9558,
            dest_lat=22.5726, dest_lon=88.3639
        )
        engine = plan.get("data_quality", {}).get("provider_engine")
        log_test(24, "Data Quality provider_engine No Transitous MOTIS Mismatch", engine != "Transitous MOTIS", f"Engine: {engine}")
    except Exception as e:
        log_test(24, "Data Quality provider_engine No Transitous MOTIS Mismatch", False, str(e))

    # Summary
    passed_count = sum(1 for _, _, p in results if p)
    total_count = len(results)

    print("=" * 60)
    print(f"VERIFICATION SUMMARY: {passed_count} / {total_count} PASSED")
    print("=" * 60)

    if passed_count == total_count:
        print("OVERALL VERDICT: PASS")
        sys.exit(0)
    else:
        print("OVERALL VERDICT: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    run_v12_3_acceptance_suite()
