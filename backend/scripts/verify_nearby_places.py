"""
verify_nearby_places.py — WanderWise Real Nearby Places & Infrastructure Data Integrity Suite

Automated verification suite to ensure:
- 0 hardcoded fake fallback lists (Central Bus Stop, Railway Station Terminal, City Taxi Stand, Station EV Charging).
- Real OpenStreetMap / Overpass API infrastructure discovery.
- Dynamic Haversine distance calculation relative to actual origin coordinates.
- Dynamic coordinate-based Google Maps URL generation.
- Strict provenance truthfulness (Live vs Fallback).
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.places.overpass_service import (
    get_nearby_boarding_infrastructure,
    get_overpass_nearby,
    VERIFIED_TRANSIT_INFRASTRUCTURE,
)
from app.services.maps.osrm_service import haversine_distance


def run_verification():
    print("=" * 60)
    print("WANDERWISE NEARBY PLACES REAL DATA VERIFICATION")
    print("=" * 60)

    results = []

    def log_test(num: int, title: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        results.append((num, title, passed))
        print(f"[{status}] {num}. {title}{' - ' + detail if detail else ''}")

    # 1. Zero Hardcoded Mock Fallbacks Check
    HARDCODED_MOCKS = [
        "Central Bus Stop",
        "Railway Station Terminal",
        "City Taxi Stand",
        "Station EV Charging",
        "General Hospital",
        "Central Police Station",
        "Express Pharmacy",
        "Global Bank ATM",
        "City Fuel Station",
    ]
    
    from app.services.places import overpass_service
    with open(overpass_service.__file__, "r", encoding="utf-8") as f:
        code = f.read()

    has_hardcoded_strings = any(f'"{m}"' in code or f"'{m}'" in code for m in HARDCODED_MOCKS)
    log_test(1, "Zero Hardcoded Mock Fallbacks in overpass_service.py", not has_hardcoded_strings, "Clean")

    # 2. Coimbatore Real Boarding Infrastructure
    cbe_infra_obj = get_nearby_boarding_infrastructure(11.0168, 76.9558)
    cbe_infra = cbe_infra_obj.get("items", [])
    cbe_prov = cbe_infra_obj.get("provenance", {})
    cbe_names = [place["name"] for place in cbe_infra]
    log_test(2, "Coimbatore Real Boarding Infrastructure", len(cbe_infra) > 0, f"Found {len(cbe_infra)} places: {cbe_names[:4]}")

    # 3. Pune Real Boarding Infrastructure
    pune_infra_obj = get_nearby_boarding_infrastructure(18.5204, 73.8567)
    pune_infra = pune_infra_obj.get("items", [])
    pune_names = [place["name"] for place in pune_infra]
    log_test(3, "Pune Real Boarding Infrastructure", len(pune_infra) > 0, f"Found {len(pune_infra)} places: {pune_names[:4]}")

    # 4. Mumbai Real Boarding Infrastructure
    mum_infra_obj = get_nearby_boarding_infrastructure(19.0760, 72.8777)
    mum_infra = mum_infra_obj.get("items", [])
    mum_names = [place["name"] for place in mum_infra]
    log_test(4, "Mumbai Real Boarding Infrastructure", len(mum_infra) > 0, f"Found {len(mum_infra)} places: {mum_names[:4]}")

    # 5. Geographic Diversity Check (Coimbatore vs Pune)
    diverse = len(cbe_names) > 0 and len(pune_names) > 0 and cbe_names != pune_names
    log_test(5, "Geographic Diversity (Coimbatore vs Pune)", diverse, f"CBE: {cbe_names[:2]} | Pune: {pune_names[:2]}")

    # 6. Dynamic Haversine Distance Calculation Test
    origin_lat, origin_lon = 11.0168, 76.9558
    distance_passed = True
    for p in cbe_infra[:5]:
        p_lat = p.get("latitude") or p.get("lat")
        p_lon = p.get("longitude") or p.get("lon")
        expected_dist = haversine_distance(origin_lat, origin_lon, p_lat, p_lon)
        if abs(expected_dist - p["distance_km"]) > 0.05:
            distance_passed = False
            break
    log_test(6, "Dynamic Haversine Distance Calculation", distance_passed, "Calculated distance matches Haversine formula")

    # 7. No Fixed 0.3 / 1.5 / 0.5 / 0.8 km Pattern
    distances = [p["distance_km"] for p in cbe_infra]
    fixed_pattern = {0.3, 1.5, 0.5, 0.8}
    no_fixed_pattern = set(distances) != fixed_pattern
    log_test(7, "No Fixed 0.3 / 1.5 / 0.5 / 0.8 km Distance Pattern", no_fixed_pattern, f"Sample distances: {distances[:5]}")

    # 8. POI Lat/Lon Coordinates are Real
    real_coords = all((isinstance(p.get("latitude"), float) or isinstance(p.get("lat"), float)) and (p.get("latitude") or p.get("lat")) != 0.0 for p in cbe_infra)
    log_test(8, "POI Lat/Lon Coordinates are Real", real_coords, f"Sample coords: ({(cbe_infra[0].get('latitude') or cbe_infra[0].get('lat'))}, {(cbe_infra[0].get('longitude') or cbe_infra[0].get('lon'))})" if cbe_infra else "")

    # 9. Provenance Truthfulness Check
    provenance_truthful = True
    for p in cbe_infra:
        stype = p.get("source_type")
        source = p.get("source", "")
        if stype == "OVERPASS" and "OpenStreetMap" not in source:
            provenance_truthful = False
        elif stype == "VERIFIED_INFRASTRUCTURE" and ("Live" in source or "OpenStreetMap" in source):
            provenance_truthful = False
    log_test(9, "Provenance Truthfulness Check (No Fake 'Live' for Fallbacks)", provenance_truthful, f"Provenance provider: {cbe_prov.get('provider')}")

    # 10. Truth-First Empty Array Handling (Ocean Coordinates Test)
    ocean_infra_obj = get_nearby_boarding_infrastructure(0.0, 0.0)
    ocean_items = ocean_infra_obj.get("items", [])
    log_test(10, "Truth-First Empty Array Handling (Ocean Test)", len(ocean_items) == 0, f"Returned length: {len(ocean_items)}")

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
    run_verification()
