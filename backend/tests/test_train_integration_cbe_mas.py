"""
test_train_integration_cbe_mas.py — WanderWise Multimodal Transit Assistant V12.2
Audit & Verification Tests for Train Transport Integration:
Origin: Coimbatore Junction (CBE)
Destination: Chennai Central (MAS)
Date: 18 November 2026 (Wednesday)

Truth-First Validation:
1. Authenticity of train numbers, names, and timetables against authorized railway data.
2. No fabricated train numbers, timings, platforms, fares, or delays.
3. Strict data provenance: LIVE_VERIFIED, SCHEDULE_VERIFIED, UNAVAILABLE.
4. Correct timezone awareness (Asia/Kolkata, UTC+05:30).
5. Realistic railway junction boarding buffer (20 minutes).
6. Authentic railway track geometry and intermediate halts (not OSRM driving directions).
7. Mode separation: trains, flights, and road routes kept separate.
8. Zero fabricated trains when no railway connection exists.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import pytest
from datetime import datetime, date, timedelta
from backend.app.services.transit.providers.railradar_provider import (
    RailRadarProvider,
    parse_railradar_time,
    resolve_station_code,
    KNOWN_TRAIN_DETAILS,
    KNOWN_TRAIN_SCHEDULES,
    CBE_MAS_TRACK_GEOMETRY,
)
from backend.app.services.transit.journey_stitcher import (
    evaluate_catchability,
    stitch_door_to_door_journey,
    stitch_all_journeys,
    KOLKATA_TZ,
)
from backend.app.services.transit.route_optimizer import RouteOptimizer
from backend.app.services.transit.station_normalizer import normalize_station_name


# Test Case Constants
CBE_LAT = 11.0016
CBE_LON = 76.9628
MAS_LAT = 13.0827
MAS_LON = 80.2757
TEST_DATE_STR = "2026-11-18"  # Wednesday
TEST_DEP_TIME = "2026-11-18T10:00:00+05:30"


@pytest.fixture
def rail_provider():
    return RailRadarProvider()


# ── TEST 1: Station Code & English Normalization ───────────────────────
def test_station_resolution_and_english_normalization():
    """Verify Coimbatore and Chennai Central resolve to CBE and MAS with clean English names."""
    code_cbe, name_cbe = resolve_station_code("Coimbatore Junction", CBE_LAT, CBE_LON)
    assert code_cbe == "CBE"
    assert "COIMBATORE" in name_cbe

    code_mas, name_mas = resolve_station_code("Chennai Central", MAS_LAT, MAS_LON)
    assert code_mas == "MAS"
    assert "CHENNAI" in name_mas

    # Verify English normalizer transforms them into user-facing English
    norm_cbe = normalize_station_name("COIMBATORE JN")
    assert norm_cbe == "Coimbatore Junction"

    norm_mas = normalize_station_name("MGR CHENNAI CENTRAL")
    assert norm_mas == "Chennai Central"

    norm_per = normalize_station_name("PERAMBUR")
    assert norm_per == "Perambur"


# ── TEST 2: CBE -> MAS Timetable Accuracy on Wednesday 18 Nov 2026 ────
def test_cbe_mas_trains_on_wednesday_18_nov_2026(rail_provider):
    """
    Test that CBE -> MAS on 18 Nov 2026 returns verified IRCTC trains:
    - Kovai SF Express (12676): 15:15 -> 22:45
    - Shatabdi Express (12244): 15:05 -> 21:50
    - Cheran SF Express (12674): 22:50 -> 07:00 (+1 day)
    - Nilgiri SF Express (12672): 22:25 -> 06:25 (+1 day)
    - Vande Bharat (20644) does NOT run on Wednesdays and must be excluded!
    """
    res = rail_provider.plan_journey(
        CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
        departure_time=TEST_DEP_TIME,
        preferences={
            "origin_name": "Coimbatore Junction",
            "dest_name": "Chennai Central",
            "full_origin_name": "Coimbatore Junction, Tamil Nadu",
            "full_dest_name": "Chennai Central, Tamil Nadu",
        }
    )

    assert res.status.value == "SUCCESS"
    assert len(res.itineraries) > 0

    train_map = {itin["train_number"]: itin for itin in res.itineraries}

    # 1. Kovai SF Express (12676)
    assert "12676" in train_map, "Kovai SF Express (12676) must be present in CBE->MAS results"
    kovai = train_map["12676"]
    assert "Kovai" in kovai["train_name"]
    assert "03:15 PM" in kovai["departure_time_display"] or "15:15" in kovai["departure_time"]
    assert "10:45 PM" in kovai["arrival_time_display"] or "22:45" in kovai["arrival_time"]
    assert kovai["duration_min"] > 0
    assert kovai["distance_km"] >= 490

    # 2. Shatabdi Express (12244) runs on Wednesday
    assert "12244" in train_map, "Shatabdi Express (12244) runs on Wednesday and must be present"
    shatabdi = train_map["12244"]
    assert "Shatabdi" in shatabdi["train_name"]
    assert "03:05 PM" in shatabdi["departure_time_display"] or "15:05" in shatabdi["departure_time"]
    assert "09:50 PM" in shatabdi["arrival_time_display"] or "21:50" in shatabdi["arrival_time"]

    # 3. Vande Bharat Express (20644) does NOT run on Wednesday
    assert "20644" not in train_map, "Vande Bharat Express (20644) does NOT run on Wednesday and must be excluded"

    # 4. Cheran SF Express (12674) - Overnight train
    assert "12674" in train_map, "Cheran SF Express (12674) must be present"
    cheran = train_map["12674"]
    assert cheran["is_overnight"] is True
    assert "2026-11-18" in cheran["departure_time"]
    assert "2026-11-19" in cheran["arrival_time"]

    # 5. Nilgiri SF Express (12672) - Overnight train
    assert "12672" in train_map, "Nilgiri SF Express (12672) must be present"
    nilgiri = train_map["12672"]
    assert nilgiri["is_overnight"] is True
    assert "2026-11-18" in nilgiri["departure_time"]
    assert "2026-11-19" in nilgiri["arrival_time"]


# ── TEST 3: Strict Data Provenance & No Fabricated Fares ───────────────
def test_strict_provenance_and_no_fabricated_data(rail_provider):
    """
    Verify strict provenance rules:
    - Schedules marked SCHEDULE_VERIFIED
    - Fares marked UNAVAILABLE (never fabricated)
    - Live status marked UNAVAILABLE when not operating
    """
    res = rail_provider.plan_journey(
        CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
        departure_time=TEST_DEP_TIME,
        preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
    )

    for itin in res.itineraries:
        # Schedule Provenance
        assert itin["verification_status"] == "SCHEDULE_VERIFIED"
        assert itin["mode"] == "Train"

        # Fare must NOT be fabricated
        assert itin["fare"] is None, f"Train {itin['train_number']} has fabricated fare {itin['fare']}"
        assert "UNAVAILABLE" in itin["fare_source"]

        # Train number and name must be non-empty strings
        assert itin["train_number"].strip() != ""
        assert itin["train_name"].strip() != ""

        # Timestamps must include +05:30 (Asia/Kolkata)
        assert "+05:30" in itin["departure_time"]
        assert "+05:30" in itin["arrival_time"]


# ── TEST 4: Railway Geometry & Intermediate Halts (Not OSRM Driving) ───
def test_railway_geometry_and_intermediate_halts(rail_provider):
    """
    Selecting a train must provide:
    - Authentic intermediate halts (e.g. Tiruppur, Erode, Salem, Katpadi)
    - Railway track geometry coordinates, NOT highway road routes
    """
    res = rail_provider.plan_journey(
        CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
        departure_time=TEST_DEP_TIME,
        preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
    )

    train_map = {itin["train_number"]: itin for itin in res.itineraries}
    kovai = train_map.get("12676")
    assert kovai is not None

    # Intermediate Halts
    halts = kovai.get("intermediate_stops", [])
    assert len(halts) >= 5, "Kovai SF Express must have intermediate stops"
    halt_codes = [h.get("station_code") for h in halts]
    assert "TUP" in halt_codes, "Tiruppur must be a halt"
    assert "ED" in halt_codes, "Erode Junction must be a halt"
    assert "SA" in halt_codes, "Salem Junction must be a halt"
    assert "KPD" in halt_codes, "Katpadi Junction must be a halt"

    # Railway Track Geometry
    geom = kovai.get("geometry", [])
    assert len(geom) >= 10, "Kovai SF Express must have railway track geometry"
    assert kovai.get("geometry_source") in ("RailRadar Railway Track", "Indian Railways Corridor Track")

    # First point near Coimbatore, last point near Chennai Central
    assert abs(geom[0][0] - CBE_LAT) < 0.1
    assert abs(geom[-1][0] - MAS_LAT) < 0.1


# ── TEST 5: Timezone-Aware Departure & Date Offset ─────────────────────
def test_timezone_aware_departure_and_date_offset():
    """
    Verify departure timestamps in Asia/Kolkata (+05:30).
    Verify same-day arrival vs next-day (+1 day) arrival calculation.
    """
    base_d = date(2026, 11, 18)

    # 1. Daytime train: 15:15 dep, same day arrival
    dep_iso, dep_disp = parse_railradar_time("15:15", base_d, day_offset=1)
    arr_iso, arr_disp = parse_railradar_time("22:45", base_d, day_offset=1)
    assert dep_iso == "2026-11-18T15:15:00+05:30"
    assert dep_disp == "3:15 PM"
    assert arr_iso == "2026-11-18T22:45:00+05:30"
    assert arr_disp == "10:45 PM"

    # 2. Overnight train: 22:50 dep, next day 07:00 arrival (day_offset=2)
    dep_ovn, dep_disp_ovn = parse_railradar_time("22:50", base_d, day_offset=1)
    arr_ovn, arr_disp_ovn = parse_railradar_time("07:00", base_d, day_offset=2)
    assert dep_ovn == "2026-11-18T22:50:00+05:30"
    assert arr_ovn == "2026-11-19T07:00:00+05:30"
    assert "(+1 day)" in arr_disp_ovn


# ── TEST 6: Realistic 20-Minute Railway Junction Boarding Buffer ───────
def test_realistic_20_minute_railway_boarding_buffer():
    """
    Catchability calculation for trains must use realistic station junction buffer:
    - 20 minutes for railway junctions (foot overbridges, rake lengths)
    - Rejects departures where user arrives with less than 20 mins buffer
    - Accepts departures with >= 20 mins buffer
    """
    station_now = datetime(2026, 11, 18, 14, 0, 0, tzinfo=KOLKATA_TZ)  # 02:00 PM
    dep_dt_soon = datetime(2026, 11, 18, 14, 25, 0, tzinfo=KOLKATA_TZ)  # 02:25 PM (departs in 25 mins)
    dep_dt_later = datetime(2026, 11, 18, 15, 15, 0, tzinfo=KOLKATA_TZ) # 03:15 PM (departs in 75 mins)

    # User takes 10 mins first-mile walk to station
    # Required buffer: 10 min walk + 20 min junction buffer = 30 min total access time
    # dep_dt_soon is at +25 mins (< 30 mins) -> CANNOT_CATCH
    is_catchable, status, msg, wait_min = evaluate_catchability(
        service_dep_dt=dep_dt_soon,
        now=station_now,
        first_mile_dur_min=10.0,
        boarding_buffer_min=20.0,
        station_name="Coimbatore Junction"
    )
    assert is_catchable is False
    assert status == "CANNOT_CATCH"
    assert "20 min station junction buffer" in msg

    # dep_dt_later is at +75 mins (>= 30 mins) -> CATCHABLE
    is_catchable2, status2, msg2, wait_min2 = evaluate_catchability(
        service_dep_dt=dep_dt_later,
        now=station_now,
        first_mile_dur_min=10.0,
        boarding_buffer_min=20.0,
        station_name="Coimbatore Junction"
    )
    assert is_catchable2 is True
    assert status2 == "CATCHABLE"
    assert wait_min2 > 0


# ── TEST 7: Door-to-Door Journey Stitching Preserves Railway Integrity ──
def test_journey_stitching_preserves_rail_integrity(rail_provider):
    """
    Test that stitch_door_to_door_journey:
    - Preserves railway track geometry and intermediate stops on the main transit leg
    - Sets railway junction buffer to 20 minutes
    - Preserves SCHEDULE_VERIFIED status
    - Keeps fare as None (UNAVAILABLE)
    """
    res = rail_provider.plan_journey(
        CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
        departure_time=TEST_DEP_TIME,
        preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
    )
    train_map = {itin["train_number"]: itin for itin in res.itineraries}
    kovai = train_map["12676"]

    # Stitch door-to-door journey from Coimbatore user location to Chennai destination
    journey = stitch_door_to_door_journey(
        route=kovai,
        origin_name="Coimbatore Junction",
        origin_lat=CBE_LAT,
        origin_lon=CBE_LON,
        dest_name="Chennai Central",
        dest_lat=MAS_LAT,
        dest_lon=MAS_LON,
        request_time=datetime(2026, 11, 18, 10, 0, 0, tzinfo=KOLKATA_TZ),
        date_hint="Tomorrow"
    )

    assert journey is not None
    assert journey["train_number"] == "12676"
    assert journey["verification_status"] in ("SCHEDULE_VERIFIED", "PROVIDER_VERIFIED")
    assert journey["fare"] is None
    assert len(journey["intermediate_stops"]) >= 5
    assert len(journey["geometry"]) >= 10

    # Main leg must be Train with RailRadar provider
    main_legs = [l for l in journey["legs"] if l["type"] == "MAIN_TRANSIT"]
    assert len(main_legs) == 1
    m_leg = main_legs[0]
    assert m_leg["mode"] in ("Train", "Rail")
    assert m_leg["provider"] in ("RailRadar", "Indian Railways Timetable")
    assert m_leg["train_number"] == "12676"
    assert len(m_leg["intermediate_stops"]) >= 5
    assert len(m_leg["geometry"]) >= 10


# ── TEST 8: Zero Fabricated Trains on Disconnected Station Pairs ───────
def test_no_fabricated_trains_on_disconnected_routes(rail_provider):
    """
    Searching for an unconnected pair (e.g. Coimbatore to London or Port Blair)
    must return NO_ITINERARY. Never fabricate trains!
    """
    res = rail_provider.plan_journey(
        CBE_LAT, CBE_LON, 51.5074, -0.1278,
        departure_time=TEST_DEP_TIME,
        preferences={"origin_name": "Coimbatore Junction", "dest_name": "London"}
    )
    assert res.status.value == "NO_ITINERARY"
    assert len(res.itineraries) == 0
    assert "zero matching train itineraries" in res.note.lower()
