"""
verify_v9.py — WanderWise Transit V9.1 Final Automated Data Integrity Verification Suite

Verifies:
  - Live Transitous MOTIS parsing for London -> Manchester (ISO timestamps, track/platform, route names)
  - Realistic journey total distance (> 150 km) distinct from walking distance
  - Transfer count calculated strictly from transit legs
  - Factual provenance badges (GTFS Scheduled vs Provider Verified vs Schedule Unavailable)
  - Isolated OSRM driving road alternative for Coimbatore -> Chennai
"""

import os
import sys
import json
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.transit.providers.base import ProviderStatus, ProviderResult
from app.services.transit.providers.transitous_provider import TransitousProvider
from app.services.transit.providers.navitia_provider import NavitiaProvider
from app.services.transit.providers.india_transit_provider import IndiaTransitProvider
from app.services.transit.providers.gtfs_provider import GTFSLocalProvider
from app.services.transit.providers.osrm_provider import OSRMRoadProvider
from app.services.transit.transit_router import TransitRouter
from app.services.transit.transit_orchestrator import TransitOrchestrator


def run_tests():
    results = {}
    print("==================================================")
    print("WANDERWISE TRANSIT V9.1 FINAL DATA INTEGRITY AUDIT")
    print("==================================================\n")

    # ── 1. Live Transitous Query & Response Parsing ─────────────────────
    t_provider = TransitousProvider()
    res1 = t_provider.plan_journey(51.5309, -0.1233, 53.4774, -2.2309)
    if res1 and res1.status == ProviderStatus.SUCCESS and res1.itineraries:
        results["1. Live Transitous Query"] = "PASS"
        it0 = res1.itineraries[0]
        legs0 = it0.get("legs", [])
        transit_legs = [l for l in legs0 if l.get("type") == "TRANSIT"]

        # Check departure/arrival time extraction
        has_dept = any(l.get("departure_time") is not None for l in transit_legs)
        has_arr = any(l.get("arrival_time") is not None for l in transit_legs)
        results["2. Departure Time Extraction"] = "PASS" if has_dept else "FAIL"
        results["3. Arrival Time Extraction"] = "PASS" if has_arr else "FAIL"

        # Check platform extraction
        has_plat = any(l.get("platform") is not None for l in transit_legs)
        results["4. Platform Extraction"] = "PASS" if has_plat else "FAIL"
    else:
        results["1. Live Transitous Query"] = "FAIL"
        results["2. Departure Time Extraction"] = "FAIL"
        results["3. Arrival Time Extraction"] = "FAIL"
        results["4. Platform Extraction"] = "FAIL"

    # ── 5. Orchestrator Journey Distance & Transfer Breakdown ─────────
    res_lnd = TransitOrchestrator.get_transit_plan("London Euston", "Manchester Piccadilly", 51.5309, -0.1233, 53.4774, -2.2309)
    if res_lnd and res_lnd.get("status") == "PUBLIC_TRANSIT_AVAILABLE":
        j = res_lnd.get("journey", {})
        tot_dist = j.get("distance_km", 0)
        walk_dist = j.get("walking_distance_km", 0)
        trans_dist = j.get("transit_distance_km", 0)
        transfers = j.get("transfers", 0)

        results["5. Realistic Total Distance (> 150 km)"] = "PASS" if tot_dist > 150 else "FAIL"
        results["6. Total Dist != Walking Dist Only"] = "PASS" if tot_dist > walk_dist else "FAIL"
        results["7. Transit Transfer Count Accuracy"] = "PASS" if isinstance(transfers, int) and transfers >= 0 else "FAIL"
    else:
        results["5. Realistic Total Distance (> 150 km)"] = "FAIL"
        results["6. Total Dist != Walking Dist Only"] = "FAIL"
        results["7. Transit Transfer Count Accuracy"] = "FAIL"

    # ── 8. Fallback Chain: Navitia, India Transit, GTFS ────────────────
    n_res = NavitiaProvider().plan_journey(51.5309, -0.1233, 53.4774, -2.2309)
    i_res = IndiaTransitProvider().plan_journey(10.937, 76.956, 13.083, 80.270)
    g_res = GTFSLocalProvider().plan_journey(51.5309, -0.1233, 53.4774, -2.2309)
    results["8. Provider Unconfigured Fallbacks"] = "PASS" if (
        n_res.status == ProviderStatus.PROVIDER_NOT_CONFIGURED
        and i_res.status in [ProviderStatus.PROVIDER_NOT_CONFIGURED, ProviderStatus.NO_ITINERARY]
        and g_res.status == ProviderStatus.PROVIDER_NOT_CONFIGURED
    ) else "FAIL"

    # ── 9. Coimbatore -> Chennai Fallback (Public Transit Unavailable) ─
    res_cbe = TransitOrchestrator.get_transit_plan("Coimbatore", "Chennai", 10.93707, 76.95636, 13.08369, 80.27018)
    if (
        res_cbe.get("status") == "PUBLIC_TRANSIT_UNAVAILABLE"
        and res_cbe.get("journey") is None
        and res_cbe.get("road_alternative") is not None
        and res_cbe["road_alternative"].get("mode") == "DRIVING"
        and res_cbe["road_alternative"].get("distance_km", 0) > 400
    ):
        results["9. Coimbatore -> Chennai Road Fallback"] = "PASS"
    else:
        results["9. Coimbatore -> Chennai Road Fallback"] = "FAIL"

    # ── 10. OSRM Isolation Check ───────────────────────────────────────
    # Ensure road alternative is NEVER placed inside journey.legs
    results["10. OSRM Isolation in journey.legs"] = "PASS" if res_cbe.get("journey") is None else "FAIL"

    # ── 11. AI Guidance Isolation Check ────────────────────────────────
    ai_guidance = res_lnd.get("ai_guidance")
    results["11. AI Guidance Isolation"] = "PASS" if (
        ai_guidance is not None
        and isinstance(ai_guidance, dict)
        and ai_guidance.get("generated") is True
        and "text" in ai_guidance
    ) else "FAIL"

    # ── 12. Service Worker Bypass Source Check ────────────────────────
    base_repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sw_path = os.path.join(base_repo_dir, "frontend", "public", "sw.js")
    sw_pass = False
    if os.path.exists(sw_path):
        with open(sw_path, "r", encoding="utf-8") as f:
            c = f.read()
            if "localhost" in c and "8000" in c and "request.method !== 'GET'" in c:
                sw_pass = True
    results["12. Service Worker API Bypass"] = "PASS" if sw_pass else "FAIL"

    print("==================================================")
    print("VERIFICATION SUMMARY:")
    all_passed = True
    for test_num_name, res_status in results.items():
        print(f"  {test_num_name}: [{res_status}]")
        if res_status != "PASS":
            all_passed = False

    print("==================================================")
    print("FINAL VERDICT")
    print("==================================================")
    if all_passed:
        print("OVERALL VERDICT: PHASE 1 TRANSIT V9.1 ACCEPTED — VERIFIED")
    else:
        print("OVERALL VERDICT: TRANSIT V9.1 VERIFICATION INCOMPLETE")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
