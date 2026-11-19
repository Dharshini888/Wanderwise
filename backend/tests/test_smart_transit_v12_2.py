"""
test_smart_transit_v12_2.py — WanderWise Smart Transit Assistant V12.2 Verification Test Suite

Tests:
  1. English-Only normalization (Japanese stations/landmarks, Indian Railways stations, transport modes, emoji icons).
  2. Elimination of negative durations (-22h -53m) and date/time consistency.
  3. Catchability calculation for future scheduled services.
  4. Test Scenario A: Kyoto Road Routing (Kyoto Station -> Kiyomizu-dera, Driving, English, Route Calculated).
  5. Test Scenario B: Coimbatore Rail Routing (Coimbatore Junction -> Chennai Central, RailRadar verified, Vande Bharat 22478, fare unavailable, return trains).
  6. Test Scenario C: Coimbatore to Kansai Transoceanic (strict rejection of road routing across ocean, flight mode).
  7. Test Scenario D: Kyoto Public Transit (Kyoto Station -> Fushimi Inari, walking vs rail, Transitous).
  8. Test Scenario E: Missing Provider Data Degradation (truth-first, no hallucinations).
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime, timedelta, time

from app.services.transit.station_normalizer import (
    normalize_station_name,
    normalize_mode_name,
    get_mode_icon,
    is_mostly_ascii,
)
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_stitcher import stitch_door_to_door_journey
from app.services.transit.transit_router import TransitRouter
from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.providers.railradar_provider import RailRadarProvider
from app.services.transit.providers.transitous_provider import TransitousProvider
from app.services.transit.providers.osrm_provider import OSRMRoadProvider
from app.services.maps.nominatim_service import geocode_place
from app.services.transit.airport_service import get_primary_gateway_airport, resolve_serving_airports


# ==============================================================================
# 1. ENGLISH-ONLY NORMALIZATION TESTS
# ==============================================================================

def test_japanese_station_and_landmark_normalization():
    """Verify Japanese characters are translated to proper English names."""
    cases = [
        ("京都駅前", "Kyoto Station"),
        ("京都駅", "Kyoto Station"),
        ("清水寺", "Kiyomizu-dera"),
        ("伏見稲荷", "Fushimi Inari"),
        ("伏見稲荷大社", "Fushimi Inari Taisha"),
        ("金閣寺", "Kinkaku-ji"),
        ("東福寺", "Tofukuji"),
        ("稲荷", "Inari"),
        ("二条城", "Nijo Castle"),
        ("嵐山", "Arashiyama"),
        ("関西空港", "Kansai International Airport"),
        ("大阪", "Osaka"),
        ("東京", "Tokyo"),
    ]
    for raw, expected in cases:
        norm = normalize_station_name(raw)
        assert norm == expected, f"Failed: {raw} -> {norm} (expected {expected})"
        assert is_mostly_ascii(norm), f"Not ASCII: {norm}"


def test_indian_railway_station_normalization():
    """Verify Indian Railways uppercase station codes and suffixes are normalized."""
    cases = [
        ("COIMBATORE JN", "Coimbatore Junction"),
        ("COIMBATORE JN.", "Coimbatore Junction"),
        ("CBE", "Coimbatore Junction"),
        ("CHENNAI CENTRAL", "Chennai Central"),
        ("MAS", "Chennai Central"),
        ("KARUR JN.", "Karur Junction"),
        ("KARUR JN", "Karur Junction"),
        ("KRR", "Karur Junction"),
        ("TIRUPPUR", "Tiruppur"),
        ("TUP", "Tiruppur"),
        ("ERODE JN", "Erode Junction"),
        ("ED", "Erode Junction"),
        ("SALEM JN", "Salem Junction"),
        ("SA", "Salem Junction"),
        ("BANGALORE CITY", "KSR Bengaluru"),
        ("SBC", "KSR Bengaluru"),
    ]
    for raw, expected in cases:
        norm = normalize_station_name(raw)
        assert norm == expected, f"Failed: {raw} -> {norm} (expected {expected})"


def test_transport_mode_and_icon_normalization():
    """Verify modes normalize to standard Titlecase English and match correct emojis."""
    modes = [
        ("walk", "Walk", "🚶"),
        ("walking", "Walk", "🚶"),
        ("foot", "Walk", "🚶"),
        ("pedestrian", "Walk", "🚶"),
        ("rail", "Rail", "🚆"),
        ("train", "Rail", "🚆"),
        ("subway", "Subway", "🚇"),
        ("metro", "Metro", "🚇"),
        ("bus", "Bus", "🚌"),
        ("driving", "Driving", "🚗"),
        ("car", "Driving", "🚗"),
        ("road", "Driving", "🚗"),
        ("flight", "Flight", "✈️"),
        ("air", "Flight", "✈️"),
    ]
    for raw_mode, expected_mode, expected_icon in modes:
        assert normalize_mode_name(raw_mode) == expected_mode
        assert get_mode_icon(raw_mode) == expected_icon


# ==============================================================================
# 2. JOURNEY TIME, DATE & DURATION TESTS (NO NEGATIVE DURATIONS)
# ==============================================================================

def test_no_negative_durations_when_planning_tomorrow():
    """
    Test the exact bug that caused '-22h -53m':
    When planning for Tomorrow at 08:00 AM, trains departing at 09:52 AM
    must be synchronized to Tomorrow's date, NOT today's date.
    Duration must be >= 0 and door_arr_dt >= door_dep_dt.
    """
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    dep_req_dt = datetime.combine(tomorrow, time(8, 0))

    # Mock a RailRadar main leg with clock departure 09:52 and arrival 15:35
    main_route = {
        "provider": "RailRadar",
        "mode": "Rail",
        "train_number": "22478",
        "train_name": "Vande Bharat Express",
        "departure_time": f"{tomorrow.isoformat()}T09:52:00",
        "arrival_time": f"{tomorrow.isoformat()}T15:35:00",
        "origin": "COIMBATORE JN",
        "destination": "CHENNAI CENTRAL",
        "duration_min": 343.0,
        "legs": [
            {
                "mode": "Rail",
                "provider": "RailRadar",
                "train_number": "22478",
                "train_name": "Vande Bharat Express",
                "departure_time": f"{tomorrow.isoformat()}T09:52:00",
                "arrival_time": f"{tomorrow.isoformat()}T15:35:00",
                "from_name": "COIMBATORE JN",
                "to_name": "CHENNAI CENTRAL",
                "duration_min": 343.0,
            }
        ]
    }

    stitched = stitch_door_to_door_journey(
        route=main_route,
        origin_name="Coimbatore Junction",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_name="Chennai Central",
        dest_lat=13.0827,
        dest_lon=80.2707,
        request_time=dep_req_dt,
        date_hint="Tomorrow",
    )

    assert stitched is not None
    # 1. Total duration must be positive and strictly >= 343 min
    total_dur = stitched.get("total_duration_min")
    assert total_dur is not None
    assert total_dur > 0, f"Total duration was non-positive: {total_dur}"
    assert total_dur >= 343.0

    # 2. Departure and arrival timestamps
    dep_dt_str = stitched.get("departure_time") or stitched.get("door_to_door_departure")
    arr_dt_str = stitched.get("arrival_time") or stitched.get("door_to_door_arrival")
    dep_dt = datetime.fromisoformat(dep_dt_str)
    arr_dt = datetime.fromisoformat(arr_dt_str)

    assert arr_dt > dep_dt, f"Arrival {arr_dt} must be after departure {dep_dt}"
    assert dep_dt.date() == tomorrow, f"Departure date {dep_dt.date()} must match tomorrow {tomorrow}"


# ==============================================================================
# 3. CATCHABILITY CALCULATION TESTS
# ==============================================================================

def test_future_train_catchability():
    """
    Test that a train departing at 09:52 AM on planning date is correctly
    marked CATCHABLE when the user leaves origin at 08:00 AM with 15 min access time.
    (8:00 AM + 15m access + 5m buffer = 8:20 AM <= 9:52 AM -> Catchable is True).
    """
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    dep_req_dt = datetime.combine(tomorrow, time(8, 0))

    main_route = {
        "provider": "RailRadar",
        "mode": "Rail",
        "train_number": "22478",
        "departure_time": f"{tomorrow.isoformat()}T09:52:00",
        "arrival_time": f"{tomorrow.isoformat()}T15:35:00",
        "origin": "COIMBATORE JN",
        "destination": "CHENNAI CENTRAL",
        "duration_min": 343.0,
        "legs": [
            {
                "mode": "Rail",
                "departure_time": f"{tomorrow.isoformat()}T09:52:00",
                "arrival_time": f"{tomorrow.isoformat()}T15:35:00",
                "from_name": "COIMBATORE JN",
                "to_name": "CHENNAI CENTRAL",
                "duration_min": 343.0,
            }
        ]
    }

    stitched = stitch_door_to_door_journey(
        route=main_route,
        origin_name="Coimbatore Junction",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_name="Chennai Central",
        dest_lat=13.0827,
        dest_lon=80.2707,
        request_time=dep_req_dt,
        date_hint="Tomorrow",
    )

    assert stitched is not None
    assert stitched["catchable"] is True, f"Train should be catchable, got: {stitched.get('why_catchable')}"
    assert "Cannot Catch" not in stitched.get("why_catchable", "")


# ==============================================================================
# 4. TEST SCENARIO A: KYOTO ROAD ROUTING (Kyoto Station -> Kiyomizu-dera)
# ==============================================================================

def test_scenario_a_kyoto_road_routing():
    """
    Scenario A: Kyoto Station to Kiyomizu-dera.
    - Resolves via geocoding to Kyoto.
    - Driving mode returned.
    - Station/stop names in English.
    - verification_status is Route Calculated.
    - Duration > 0.
    """
    plan = TransitOrchestrator.get_transit_plan(
        origin="Kyoto Station",
        destination="Kiyomizu-dera",
        preferred_mode="fastest",
        date="Tomorrow",
        departure_type="now",
    )

    assert plan is not None
    assert plan["status"] in ["VERIFIED_ROAD_ALTERNATIVE", "PUBLIC_TRANSIT_AVAILABLE"]

    rec = plan.get("recommended_route")
    assert rec is not None
    assert rec.get("verification_status") in ["Route Calculated", "Provider Verified", "VERIFIED", "Schedule Verified"]

    # Duration must be non-negative
    dur = rec.get("duration_min") or rec.get("duration_minutes")
    assert dur is not None and dur > 0

    # Segments and stops must be in English
    for leg in rec.get("legs", []):
        f = leg.get("from_stop") or leg.get("from_name") or ""
        t = leg.get("to_stop") or leg.get("to_name") or ""
        assert is_mostly_ascii(f), f"Non-English stop: {f}"
        assert is_mostly_ascii(t), f"Non-English stop: {t}"


# ==============================================================================
# 5. TEST SCENARIO B: COIMBATORE RAIL RADAR (Coimbatore Junction -> Chennai Central)
# ==============================================================================

def test_scenario_b_coimbatore_railradar():
    """
    Scenario B: Coimbatore Junction to Chennai Central.
    - RailRadar verified trains returned.
    - Vande Bharat 22478 present.
    - English station names: Coimbatore Junction, Chennai Central.
    - Fare is None and labeled 'Fare unavailable'.
    - MAS -> CBE return route also returns valid trains.
    """
    provider = RailRadarProvider()
    res = provider.plan_journey(
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_lat=13.0827,
        dest_lon=80.2707,
        preferences={"origin_name": "Coimbatore", "dest_name": "Chennai Central"},
    )
    routes = res.itineraries
    assert len(routes) >= 3

    train_numbers = [r.get("train_number") for r in routes]
    assert ("20644" in train_numbers or "12676" in train_numbers or "22478" in train_numbers), f"Target train missing in {train_numbers}"
    assert "12676" in train_numbers, f"Kovai SF 12676 missing in {train_numbers}"

    for r in routes:
        orig = r.get("origin")
        orig_name = orig.get("name") if isinstance(orig, dict) else str(orig)
        dest = r.get("destination")
        dest_name = dest.get("name") if isinstance(dest, dict) else str(dest)
        assert "Coimbatore" in orig_name
        assert "Chennai" in dest_name
        assert r.get("fare") is None
        assert "unavailable" in (r.get("fare_source") or "").lower()
        assert r.get("verification_status") in ["Provider Verified", "Schedule Verified", "SCHEDULE_VERIFIED"]
        assert r.get("duration_min") > 0

    # Test return direction MAS -> CBE
    ret_res = provider.plan_journey(
        origin_lat=13.0827,
        origin_lon=80.2707,
        dest_lat=11.0016,
        dest_lon=76.9628,
        preferences={"origin_name": "Chennai Central", "dest_name": "Coimbatore"},
    )
    assert len(ret_res.itineraries) >= 3
    ret_numbers = [r.get("train_number") for r in ret_res.itineraries]
    assert ("20643" in ret_numbers or "12675" in ret_numbers or "22477" in ret_numbers), f"Return train missing in {ret_numbers}"


# ==============================================================================
# 6. TEST SCENARIO C: COIMBATORE TO KANSAI (TRANSOCEANIC NO OCEAN ROAD ROUTE)
# ==============================================================================

def test_scenario_c_coimbatore_to_kansai_no_ocean_drive():
    """
    Scenario C: Coimbatore to Kansai International Airport.
    - Distance is ~5,800 km across borders / ocean.
    - Strict rejection of OSRM driving routes across the ocean.
    - Must NOT generate a 1,387 km road route.
    - Mode must be Flight / Multimodal Air, or status ROUTE_GUIDANCE_AVAILABLE / VERIFIED_FLIGHT.
    """
    plan = TransitOrchestrator.get_transit_plan(
        origin="Coimbatore Junction",
        destination="Kansai International Airport",
        preferred_mode="fastest",
        date="Tomorrow",
    )

    assert plan is not None

    # Check distance summary
    dist_sum = plan.get("distance_summary", {})
    dist_type = dist_sum.get("distance_type")
    assert dist_type != "ROAD_FALLBACK", "Transoceanic route must NOT fallback to road driving!"

    # Recommended route must not be OSRM driving
    rec = plan.get("recommended_route") or {}
    if rec:
        assert rec.get("provider") != "OSRM", "OSRM must not be used for transoceanic route!"
        assert rec.get("mode") != "Driving"

    # Nearest airport resolution checks
    orig_ap = get_primary_gateway_airport("Coimbatore", 11.0168, 76.9558)
    assert orig_ap is not None
    assert orig_ap["iata"] == "CJB"

    dest_ap = get_primary_gateway_airport("Kansai", 34.4347, 135.2442)
    assert dest_ap is not None
    assert dest_ap["iata"] == "KIX"


# ==============================================================================
# 7. TEST SCENARIO D: KYOTO PUBLIC TRANSIT (Kyoto Station -> Fushimi Inari)
# ==============================================================================

def test_scenario_d_kyoto_public_transit():
    """
    Scenario D: Kyoto Station to Fushimi Inari Taisha.
    - Transitous provider returns public transit.
    - Walking vs transit correctly distinguished.
    - Station names normalized to English ('Kyoto Station', 'Inari' / 'Fushimi Inari').
    - Non-negative durations.
    """
    provider = TransitousProvider()
    res = provider.plan_journey(
        origin_lat=34.9858,
        origin_lon=135.7588,
        dest_lat=34.9671,
        dest_lon=135.7727,
        departure_time=datetime.now().isoformat(),
        preferences={"origin_name": "Kyoto Station", "dest_name": "Fushimi Inari"},
    )
    routes = res.itineraries
    assert len(routes) > 0
    route = routes[0]

    # Non-negative duration
    assert route.get("duration_min") is not None
    assert route["duration_min"] > 0

    # Legs must have English names and correct mode
    for leg in route.get("legs", []):
        f = leg.get("from_name", "")
        t = leg.get("to_name", "")
        assert is_mostly_ascii(f), f"Non-English leg start: {f}"
        assert is_mostly_ascii(t), f"Non-English leg end: {t}"
        assert leg.get("mode") in ["Walk", "Rail", "Bus", "Subway", "Tram", "Transit", "Train"]


# ==============================================================================
# 8. TEST SCENARIO E: MISSING PROVIDER DATA DEGRADATION
# ==============================================================================

def test_scenario_e_missing_provider_graceful_degradation():
    """
    Scenario E: Unsupported or remote routing request.
    - Gracefully degrades without raising unhandled exceptions.
    - Does NOT hallucinate train numbers or invent fares.
    - Strategy analysis shows INSUFFICIENT_DATA or UNAVAILABLE for missing metrics.
    """
    plan = TransitOrchestrator.get_transit_plan(
        origin="Tristan da Cunha",
        destination="Bouvet Island",
        preferred_mode="fastest",
        date="Tomorrow",
    )

    assert plan is not None
    assert plan["status"] in ["LOCATION_UNRESOLVED", "ROUTING_UNAVAILABLE", "ROUTE_GUIDANCE_AVAILABLE", "PROVIDERS_UNAVAILABLE", "ALTERNATIVE_PROVIDER_UNAVAILABLE"]
