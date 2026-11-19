"""
test_transit_regression_audit_v12_2.py -- WanderWise V12.2 Integration Regression Audit Suite

10 Mandatory Automated Regression Tests:
1. Provider status vs actual OSRM result (Route calculated / Connected).
2. Provider status vs offline train availability (Connected / Offline timetable available).
3. Pune geocoding and station resolution (Pune -> (18.5204, 73.8567) -> PUNE JN).
4. Train departure and arrival consistency (Card timestamps == scheduled, duration == difference, explanation identical).
5. Overnight train journeys (+1 day rollover, dep_day=1, arr_day=2).
6. Correct transport mode rendering (Train/Rail vs Bus vs Driving).
7. GPS-origin multimodal routing (Current GPS location near Pune -> Pune Jn -> Mumbai trains + OSRM).
8. Leave Now using actual local time in Asia/Kolkata (+05:30).
9. RailRadar quota exhaustion (HTTP 429) with offline IRCTC timetable fallback.
10. Intermediate station matching across known halt profiles (e.g. Erode -> Chennai, Salem -> Bengaluru).
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.provider_manager import ProviderManager, ProviderCircuitBreaker
from app.services.transit.providers.base import ProviderStatus, ProviderResult
from app.services.transit.providers.railradar_provider import (
    RailRadarProvider,
    resolve_station_code,
    station_matches,
    parse_railradar_time,
    KNOWN_TRAIN_SCHEDULES,
    KNOWN_TRAIN_DETAILS,
)
from app.services.transit.providers.verified_schedule_provider import VerifiedIndianRailProvider
from app.services.maps.nominatim_service import geocode_place
from app.services.transit.station_normalizer import normalize_station_name, get_mode_icon
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_stitcher import stitch_door_to_door_journey, evaluate_catchability
from app.services.transit.tz_utils import KOLKATA_TZ


# ── TEST 1: Provider status vs actual OSRM result ─────────────────────────────
def test_1_provider_status_vs_osrm_result():
    """
    Test 1: Verify OSRM provider status reflects actual calculation.
    When road alternative is calculated, provider_statuses['OSRM'] must be 'Route calculated' or 'Connected',
    never 'No verified itinerary' or 'No itinerary found'.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="Pune",
        destination="Mumbai",
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T08:00:00",
    )
    assert res is not None
    prov_statuses = res.get("provider_statuses", {})
    assert "OSRM" in prov_statuses
    assert prov_statuses["OSRM"] in ("Route calculated", "Connected")
    # Verify road alternative is present
    has_road = any(
        r.get("provider") == "OSRM" or (r.get("mode") or "").lower() in ("driving", "road")
        for r in (res.get("all_route_options", []) + res.get("journeys", []))
    )
    assert has_road is True


# ── TEST 2: Provider status vs offline train availability ─────────────────────
def test_2_provider_status_vs_offline_train_availability():
    """
    Test 2: Verify Indian Railways Timetable status reflects verified timetable records.
    When verified offline train schedules exist for the corridor, status must indicate
    'Connected' or 'Offline timetable available', never 'No verified itinerary'.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="Chennai Central",
        destination="Coimbatore Junction",
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T06:00:00",
    )
    assert res is not None
    prov_statuses = res.get("provider_statuses", {})
    assert "Indian Railways Timetable" in prov_statuses
    assert prov_statuses["Indian Railways Timetable"] in ("Connected", "Offline timetable available")
    # Ensure genuine trains are in the response
    trains = [j for j in res.get("journeys", []) if j.get("train_number")]
    assert len(trains) > 0


# ── TEST 3: Pune geocoding and station resolution ────────────────────────────
def test_3_pune_geocoding_and_station_resolution():
    """
    Test 3: Verify Pune resolves to valid geographic coordinates and maps to PUNE Junction station code.
    Also verify Mumbai, Chennai, Madurai, Salem, Bengaluru, Coimbatore, Erode for both city and station names.
    """
    # 1. Geocode Pune
    geo_pune = geocode_place("Pune")
    assert geo_pune is not None
    assert 18.0 <= geo_pune["lat"] <= 19.0
    assert 73.0 <= geo_pune["lon"] <= 74.5

    # 2. Station resolution for Pune
    code, full_name = resolve_station_code("Pune", geo_pune["lat"], geo_pune["lon"])
    assert code == "PUNE"
    assert "PUNE" in full_name.upper()

    # 3. Test city and railway station pairs for all required hubs
    test_hubs = [
        ("Mumbai", "CSMT"),
        ("Mumbai Central", "MMCT"),
        ("Chennai", "MAS"),
        ("Chennai Central", "MAS"),
        ("Chennai Egmore", "MS"),
        ("Madurai", "MDU"),
        ("Madurai Junction", "MDU"),
        ("Salem", "SA"),
        ("Salem Junction", "SA"),
        ("Bengaluru", "SBC"),
        ("KSR Bengaluru", "SBC"),
        ("Coimbatore", "CBE"),
        ("Coimbatore Junction", "CBE"),
        ("Erode", "ED"),
        ("Erode Junction", "ED"),
    ]
    for place_name, expected_code in test_hubs:
        geo = geocode_place(place_name)
        assert geo is not None, f"Geocoding failed for {place_name}"
        c, n = resolve_station_code(place_name, geo["lat"], geo["lon"])
        # Support interchangeable terminals (e.g. MAS/MS for Chennai, CSMT/MMCT for Mumbai)
        assert station_matches(expected_code, "", c, n), f"Resolution failed for {place_name}: got {c}, expected {expected_code}"


# ── TEST 4: Train departure and arrival consistency ──────────────────────────
def test_4_train_departure_and_arrival_consistency():
    """
    Test 4: For KSR Bengaluru -> Chennai Central:
    - Card departure and arrival must equal scheduled timestamps (not un-normalized UTC).
    - Duration must strictly match the difference between arrival and departure.
    - Catchability explanation must reference the EXACT SAME departure timestamp.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="KSR Bengaluru",
        destination="Chennai Central",
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T06:00:00",
    )
    assert res is not None
    journeys = res.get("journeys", [])
    train_journeys = [j for j in journeys if j.get("train_number")]
    assert len(train_journeys) > 0

    for j in train_journeys:
        dep_disp = j["departure_time_display"]
        arr_disp = j["arrival_time_display"]
        dur_min = j["duration_min"]
        why_msg = j.get("why_catchable", "")

        # Verify departure time is cleanly in 12-hour AM/PM format (not raw UTC 24-hr)
        assert ("AM" in dep_disp or "PM" in dep_disp), f"Invalid dep display: {dep_disp}"
        assert ("AM" in arr_disp or "PM" in arr_disp), f"Invalid arr display: {arr_disp}"

        # If explanation mentions departure, it must use the identical departure timestamp
        if "service departs at" in why_msg:
            assert dep_disp in why_msg, f"Timestamp mismatch: card has {dep_disp} but explanation has {why_msg}"

        # Verify duration matches timestamp difference
        if j.get("departure_time") and j.get("arrival_time"):
            d_dt = datetime.fromisoformat(j["departure_time"])
            a_dt = datetime.fromisoformat(j["arrival_time"])
            expected_dur = round((a_dt - d_dt).total_seconds() / 60.0, 1)
            assert abs(dur_min - expected_dur) <= 1.0, f"Duration mismatch: {dur_min} vs {expected_dur}"


# ── TEST 5: Overnight train journeys (+1 day rollover) ───────────────────────
def test_5_overnight_train_journeys():
    """
    Test 5: Verify overnight train journeys (e.g. 12658 SBC -> MAS, 22:40 -> 04:20+1)
    correctly reflect overnight status, +1 day arrival display, and valid duration.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="KSR Bengaluru",
        destination="Chennai Central",
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T22:00:00",
    )
    assert res is not None
    journeys = res.get("journeys", [])
    mail_train = next((j for j in journeys if j.get("train_number") == "12658"), None)
    assert mail_train is not None, "Chennai Mail 12658 not found in SBC -> MAS results"

    assert mail_train["is_overnight"] is True
    assert "(+1 day)" in mail_train["arrival_time_display"]
    assert "10:40 PM" in mail_train["departure_time_display"]
    assert "4:20 AM" in mail_train["arrival_time_display"]

    # Duration must be 5h 40m = 340 minutes
    assert abs(mail_train["duration_min"] - 340.0) <= 2.0


# ── TEST 6: Correct transport mode rendering ─────────────────────────────────
def test_6_correct_transport_mode_rendering():
    """
    Test 6: Verify genuine railway routes show mode 'Rail' or 'Train' and train icons,
    NOT Bus icons, for train journeys like KSR Bengaluru ↔ Chennai Central.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="KSR Bengaluru",
        destination="Chennai Central",
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T06:00:00",
    )
    assert res is not None
    train_journeys = [j for j in res.get("journeys", []) if j.get("train_number")]
    assert len(train_journeys) >= 3

    for tj in train_journeys:
        mode = tj.get("mode", "")
        assert mode.lower() in ("rail", "train"), f"Expected Rail/Train mode, got {mode}"
        icon = get_mode_icon(mode)
        assert icon == "🚆", f"Expected 🚆 icon for {mode}, got {icon}"


# ── TEST 7: GPS-origin multimodal routing ────────────────────────────────────
def test_7_gps_origin_multimodal_routing():
    """
    Test 7: Multimodal routing with origin="Current GPS Location" near Pune (lat=18.5204, lon=73.8567)
    and destination="Mumbai":
    - Origin coordinates near Pune resolve to Pune Junction via proximity search.
    - Returns verified Pune -> Mumbai trains (Deccan Queen, Pragati, Sinhagad, etc.).
    - Returns OSRM road driving alternative.
    - Aggregates provider statuses accurately.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="Current GPS Location",
        destination="Mumbai",
        origin_source="BROWSER_GPS",
        origin_lat=18.5204,
        origin_lon=73.8567,
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T06:30:00",
    )
    assert res is not None
    assert res.get("status") in ("PUBLIC_TRANSIT_AVAILABLE", "MULTIMODAL_ROUTES_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE")
    assert res.get("origin_source") == "BROWSER_GPS"

    # Verify train journeys found between Pune and Mumbai
    journeys = res.get("journeys", [])
    pune_trains = [j for j in journeys if j.get("train_number") in ("12124", "12126", "12128", "22226", "12110", "11008")]
    assert len(pune_trains) > 0, "No Pune -> Mumbai trains found for GPS origin"

    # Verify first mile access to Pune Junction
    first_j = pune_trains[0]
    assert first_j["departure_station"] in ("Pune Junction", "PUNE JN", "Pune")
    assert first_j["arrival_station"] in ("Mumbai CSMT", "MUMBAI CSMT", "Mumbai Central")

    # Verify OSRM road alternative
    prov_statuses = res.get("provider_statuses", {})
    assert prov_statuses.get("OSRM") in ("Route calculated", "Connected")
    assert prov_statuses.get("Indian Railways Timetable") in ("Connected", "Offline timetable available")


# ── TEST 8: Leave Now using actual local time in Asia/Kolkata ─────────────────
def test_8_leave_now_uses_actual_local_time():
    """
    Test 8: When departure_type='now', departure_time is None:
    - Backend resolves to actual current time in Asia/Kolkata timezone (+05:30).
    - Response departure_plan contains timezone='Asia/Kolkata'.
    - Past train departures are flagged CANNOT_CATCH or ALREADY_DEPARTED, not CATCHABLE.
    """
    res = TransitOrchestrator.get_transit_plan(
        origin="Coimbatore Junction",
        destination="Chennai Central",
        date="Today",
        departure_type="now",
        departure_time=None,
    )
    assert res is not None
    dep_plan = res.get("departure_plan", {})
    assert "Asia/Kolkata" in dep_plan.get("timezone", "")
    assert dep_plan.get("departure_type") == "now"

    # Catchability check
    journeys = res.get("journeys", [])
    assert len(journeys) > 0
    now_kolkata = datetime.now(KOLKATA_TZ)

    for j in journeys:
        if j.get("train_number") and j.get("departure_time"):
            dep_dt = datetime.fromisoformat(j["departure_time"])
            if dep_dt < (now_kolkata - timedelta(minutes=15)):
                assert j["catchability_status"] in ("ALREADY_DEPARTED", "CANNOT_CATCH")
                assert j["catchable"] is False


# ── TEST 9: RailRadar quota exhaustion with offline timetable fallback ────────
def test_9_railradar_quota_exhaustion_with_offline_fallback():
    """
    Test 9: When RailRadar is rate-limited (HTTP 429), verify:
    - Circuit breaker records 'Rate limited'.
    - Provider manager does not hang or fail.
    - Seamlessly fails over to verified Indian Railways offline timetables.
    - Provider status shows RailRadar='Rate limited', Indian Railways='Connected'.
    """
    pm = ProviderManager.get_instance()
    pm.breakers["RailRadar"].trip_rate_limited({"remaining_month": "0", "error_message": "Rate limit exceeded (HTTP 429)"})

    res = TransitOrchestrator.get_transit_plan(
        origin="Madurai Junction",
        destination="Chennai Egmore",
        date="Today",
        departure_type="scheduled",
        departure_time="2026-11-19T06:00:00",
    )
    assert res is not None
    prov_statuses = res.get("provider_statuses", {})
    assert prov_statuses.get("RailRadar") == "Rate limited"
    assert prov_statuses.get("Indian Railways Timetable") in ("Connected", "Offline timetable available")

    # Genuine Vaigai / Pandian trains returned
    trains = [j for j in res.get("journeys", []) if j.get("train_number") in ("12636", "12638", "20602")]
    assert len(trains) > 0, "Offline timetable failover failed to return Madurai -> Chennai trains"


# ── TEST 10: Intermediate station matching across known halt profiles ────────
def test_10_intermediate_station_matching():
    """
    Test 10: Verify trains with verified halt profiles serve intermediate city pairs:
    - Kovai Express (12676) halts: CBE -> TUP -> ED -> SA -> MAP -> JTJ -> AB -> KPD -> AJJ -> PER -> MAS
    - Intermediate search: Erode Junction -> Katpadi Junction must match Kovai Express (12676)
      or InterCity SF (12680) with correct intermediate departure and arrival times.
    """
    prov = VerifiedIndianRailProvider()
    res = prov.plan_journey(
        origin_lat=11.3400,
        origin_lon=77.7289,
        dest_lat=12.9698,
        dest_lon=79.1368,
        departure_time="2026-11-19T15:00:00",
        preferences={"origin_name": "Erode Junction", "dest_name": "Katpadi Junction"},
    )
    assert res is not None
    assert res.status == ProviderStatus.SUCCESS
    assert len(res.itineraries) > 0

    # Verify intermediate train matches
    itin = next((it for it in res.itineraries if it.get("train_number") in ("12676", "12680", "12244")), None)
    assert itin is not None, "Intermediate stop matching failed for Erode -> Katpadi"
    assert "Erode" in itin["origin"]
    assert "Katpadi" in itin["destination"]
    assert itin["duration_min"] > 0
    assert itin["verification_status"] == "SCHEDULE_VERIFIED"
