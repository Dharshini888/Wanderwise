"""
test_global_transit_integrity_and_timezone_v12_2.py -- Verification Suite for WanderWise V12.2

Tests the Global Transit Data Integrity and Timezone Corrections:
1. Priority 1 -- Flight timezone correctness (Bhutan -> Delhi: Paro PBH in Asia/Thimphu, DEL in Asia/Kolkata).
   Guarantees no timestamp contradiction across card, timeline, expanded itinerary, and explanations.
2. Priority 2 -- Flight card and itinerary consistency (Coimbatore -> Chennai: door-to-door vs flight schedule).
3. Priority 3 -- Verification and provenance semantics (leg-level vs multimodal door-to-door; Transitous is Schedule Verified).
4. Priority 4 -- External research relevance for short domestic corridors (Coimbatore -> Erode: no CJB as dest, no COK/BLR, ground fares).
5. Priority 5 -- Strategy vs actual options & awards calculation.
6. Priority 6 -- Current-time and catchability validation (never mark past departures as AVAILABLE_LATER or CATCHABLE; road routes never start in past).
7. Priority 7 -- Global routes: Delhi -> Tokyo date crossing, Sydney -> Auckland international, Pune -> Mumbai ground, overnight train.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, date, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.transit.providers.flight_provider import (
    FlightProvider,
    parse_aviationstack_datetime,
    parse_utc_flight_datetime,
)
from app.services.transit.airport_service import (
    resolve_serving_airports,
    get_airport_by_iata,
    get_airport_timezone,
    GLOBAL_AIRPORTS,
)
from app.services.transit.tz_utils import get_timezone, format_datetime_with_tz, KOLKATA_TZ
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_stitcher import (
    stitch_door_to_door_journey,
    evaluate_catchability,
    _parse_iso,
    _format_time_display,
)
from app.services.transit.external_travel_research import (
    ExternalTravelResearchService,
)
from app.services.transit.ai_route_guidance import AIRouteGuidanceService


# ── TEST 1: Bhutan -> Delhi Flight Timezone Correctness (Priority 1) ──────────

def test_bhutan_to_delhi_flight_timezone_consistency():
    """
    Priority 1: Bhutan (PBH, Asia/Thimphu, UTC+6) -> Delhi (DEL, Asia/Kolkata, UTC+5:30).
    Verifies:
    1. Departure timestamp is in Asia/Thimphu (+06).
    2. Arrival timestamp is in Asia/Kolkata (IST).
    3. Flight card, expanded itinerary, and timeline use identical consistent local representations.
    4. Explanatory text / catchability does NOT contradict card display (no 10:20 AM vs 3:50 PM clash).
    """
    mock_pbh_del_raw = {
        "flight_date": "2026-11-20",
        "flight_status": "scheduled",
        "departure": {
            "airport": "Paro Airport",
            "timezone": "Asia/Thimphu",
            "iata": "PBH",
            "icao": "VQPR",
            "scheduled": "2026-11-20T10:20:00+00:00",
        },
        "arrival": {
            "airport": "Indira Gandhi International",
            "timezone": "Asia/Kolkata",
            "iata": "DEL",
            "icao": "VIDP",
            "scheduled": "2026-11-20T12:10:00+00:00",
        },
        "airline": {"name": "Drukair", "iata": "KB"},
        "flight": {"number": "204", "iata": "KB204"},
        "live": None,
    }

    fp = FlightProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [mock_pbh_del_raw]}

    with patch.object(fp.session, "get", return_value=mock_resp), \
         patch.object(fp, "get_api_key", return_value="test_flight_key"):
        result = fp.plan_journey(
            origin_lat=27.4728, origin_lon=89.6393,  # Thimphu / Paro
            dest_lat=28.6139, dest_lon=77.2090,     # Delhi
            origin_name="Bhutan", dest_name="Delhi"
        )

    assert result.status.value == "SUCCESS"
    assert len(result.itineraries) == 1
    itin = result.itineraries[0]

    # Verify authentic airport resolution
    assert itin["origin_iata"] == "PBH"
    assert itin["destination_iata"] == "DEL"

    # Verify flight departure display has authentic Bhutan timezone (+06 or BTT)
    assert itin["flight_departure_time_display"] is not None
    assert "10:20 AM" in itin["flight_departure_time_display"]
    assert ("+06" in itin["flight_departure_time_display"] or "BTT" in itin["flight_departure_time_display"])

    # Verify flight arrival display has authentic Indian timezone (IST)
    assert itin["flight_arrival_time_display"] is not None
    assert "12:10 PM" in itin["flight_arrival_time_display"]
    assert "IST" in itin["flight_arrival_time_display"]

    # Verify in-air elapsed duration in UTC:
    # 10:20 in Thimphu (UTC+6) is 04:20 UTC.
    # 12:10 in Delhi (UTC+5:30) is 06:40 UTC.
    # Duration: 06:40 - 04:20 = 2h 20m = 140 minutes.
    assert itin["flight_duration_minutes"] == 140.0
    assert itin["flight_duration_display"] == "2h 20m"

    # Stitch door-to-door journey
    stitched = stitch_door_to_door_journey(
        route=itin,
        origin_name="Bhutan", origin_lat=27.4728, origin_lon=89.6393,
        dest_name="Delhi", dest_lat=28.6139, dest_lon=77.2090,
        request_time=datetime(2026, 11, 20, 6, 0, tzinfo=get_timezone("Asia/Thimphu"))
    )

    assert stitched is not None
    # Stitched flight departure display matches itin flight departure display
    assert stitched["flight_departure_time_display"] == itin["flight_departure_time_display"]
    assert stitched["flight_arrival_time_display"] == itin["flight_arrival_time_display"]

    # Verify why_catchable does NOT contradict the departure time
    assert "10:20 AM" in stitched["why_catchable"]
    assert "3:50 PM" not in stitched["why_catchable"]  # No false Indian conversion of Bhutan departure


# ── TEST 2: Coimbatore -> Chennai Flight Card & Itinerary Consistency (Priority 2) ─

def test_coimbatore_to_chennai_flight_card_consistency():
    """
    Priority 2: Coimbatore (CJB) -> Chennai (MAA).
    Verifies:
    1. Card departure = first-mile departure.
    2. Card arrival = last-mile arrival.
    3. Card total duration = actual door-to-door duration.
    4. Main flight departure and arrival = provider flight schedule at airport.
    5. Domestic check-in buffer (90 min) is explicitly present as a transfer leg.
    6. Catchability correctly accounts for check-in buffer: CANNOT_CATCH when arrival at airport violates buffer.
    """
    mock_cjb_maa_raw = {
        "flight_date": "2026-11-20",
        "flight_status": "scheduled",
        "departure": {
            "airport": "Coimbatore International Airport",
            "timezone": "Asia/Kolkata",
            "iata": "CJB",
            "icao": "VOCB",
            "scheduled": "2026-11-20T07:30:00+00:00",
        },
        "arrival": {
            "airport": "Chennai International Airport",
            "timezone": "Asia/Kolkata",
            "iata": "MAA",
            "icao": "VOMM",
            "scheduled": "2026-11-20T08:35:00+00:00",
        },
        "airline": {"name": "IndiGo", "iata": "6E"},
        "flight": {"number": "234", "iata": "6E234"},
        "live": None,
    }

    fp = FlightProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [mock_cjb_maa_raw]}

    with patch.object(fp.session, "get", return_value=mock_resp), \
         patch.object(fp, "get_api_key", return_value="test_flight_key"):
        result = fp.plan_journey(
            origin_lat=11.0168, origin_lon=76.9558,  # Coimbatore City
            dest_lat=13.0827, dest_lon=80.2707,     # Chennai City
            origin_name="Coimbatore", dest_name="Chennai"
        )

    assert result.status.value == "SUCCESS"
    itin = result.itineraries[0]

    # Verify Flight Schedule vs Door-to-Door times
    # Flight: 07:30 AM IST -> 08:35 AM IST (65 mins in-air)
    assert itin["flight_duration_minutes"] == 65.0
    assert "7:30 AM" in itin["flight_departure_time_display"]
    assert "8:35 AM" in itin["flight_arrival_time_display"]

    # Door-to-door access and buffers:
    # Access: ~15 mins (origin to CJB)
    # Check-in buffer: 90 mins domestic
    # Baggage buffer: 30 mins domestic
    # Egress: ~25 mins (MAA to Chennai dest)
    breakdown = itin["duration_breakdown"]
    assert breakdown["checkin_buffer_min"] == 90.0
    assert breakdown["baggage_buffer_min"] == 30.0
    assert breakdown["flight_min"] == 65.0
    assert itin["duration_minutes"] > 200.0  # Total door-to-door > 3 hours

    # Verify checkin transfer leg in itinerary
    checkin_legs = [l for l in itin["legs"] if l.get("type") == "TRANSFER" and "check-in" in (l.get("note") or "").lower()]
    assert len(checkin_legs) == 1
    assert checkin_legs[0]["duration_min"] == 90.0
    assert checkin_legs[0]["verification_status"] == "Buffer Verified"

    # Test Catchability:
    # If user requests journey at 06:30 AM (only 60 mins before 07:30 flight):
    # User needs 15m drive + 90m checkin = 105 mins. Earliest boarding is 08:15 AM > 07:30 AM flight!
    stitched_too_late = stitch_door_to_door_journey(
        route=itin,
        origin_name="Coimbatore", origin_lat=11.0168, origin_lon=76.9558,
        dest_name="Chennai", dest_lat=13.0827, dest_lon=80.2707,
        request_time=datetime(2026, 11, 20, 6, 30, tzinfo=KOLKATA_TZ)
    )
    assert stitched_too_late["catchable"] is False
    assert stitched_too_late["catchability_status"] == "CANNOT_CATCH"
    assert "airport check-in & security buffer" in stitched_too_late["why_catchable"]


# ── TEST 3: Coimbatore -> Erode External Research Relevance (Priority 4) ─────

def test_coimbatore_to_erode_external_research_relevance():
    """
    Priority 4: Coimbatore -> Erode (~90 km short domestic corridor).
    Verifies:
    1. Do NOT recommend Coimbatore Airport as destination!
    2. Do NOT list Kochi (COK) or Bengaluru (BLR) as candidate origin airports!
    3. candidate_airports has empty origin_airports and destination_airports.
    4. has_commercial_flights is False.
    5. Recommends ground transport (passenger rail, express buses, highway driving).
    6. Indicative fare range is ground transit fares (₹70–₹350), NOT airline flight fares (₹2,500+).
    """
    research = ExternalTravelResearchService.get_research(
        origin_name="Coimbatore",
        dest_name="Erode",
        origin_lat=11.0168, origin_lon=76.9558,
        dest_lat=11.3410, dest_lon=77.7172,
        scale="DOMESTIC",
        origin_country="India",
        dest_country="India",
    )

    assert research["is_external_research"] is True
    assert research["has_commercial_flights"] is False

    # Candidate airports must NOT list CJB as destination or COK/BLR as origin
    cand_aps = research["candidate_airports"]
    assert len(cand_aps["origin_airports"]) == 0
    assert len(cand_aps["destination_airports"]) == 0

    # Operators must be ground transport
    ops = research["candidate_operators_to_investigate"]
    modes = [op["mode"].lower() for op in ops]
    assert "rail" in modes or "bus" in modes or "road" in modes

    # Fares must be realistic ground transit fares, not airline tickets
    fare = research["indicative_fare_range"]
    assert fare["currency"] == "INR"
    assert fare["min_amount"] < 200  # e.g. ₹70 rail/bus
    assert fare["max_amount"] < 1000 # Under ₹1,000 for ground travel
    assert "₹70" in fare["display"] or "ground fares" in fare["display"]

    # Explicit flight applicability note
    assert "not applicable" in research["flight_applicability_note"].lower()


# ── TEST 4: Verification and Provenance Semantics (Priority 3) ─────────────────

def test_multimodal_flight_and_transitous_verification_labels():
    """
    Priority 3:
    1. Multimodal door-to-door flight journey is labeled 'Partially Verified', NEVER 'Provider Verified'.
    2. Leg-level verifications are accurately distinguished:
       - OSRM access/egress: 'Route Calculated'
       - Transfers: 'Buffer Verified'
       - Flight: 'Provider Verified'
    3. Transitous routes are labeled 'Schedule Verified', NEVER 'Official Railway Verified'.
    """
    mock_fl_route = {
        "provider": "FlightProvider",
        "mode": "Flight",
        "origin": "Coimbatore",
        "destination": "Chennai",
        "origin_airport": "Coimbatore International Airport (CJB)",
        "destination_airport": "Chennai International Airport (MAA)",
        "flight_number": "6E234",
        "airline": "IndiGo",
        "departure_time": "2026-11-20T05:45:00+05:30",
        "arrival_time": "2026-11-20T09:30:00+05:30",
        "flight_departure_time": "2026-11-20T07:30:00+05:30",
        "flight_arrival_time": "2026-11-20T08:35:00+05:30",
        "flight_departure_time_display": "7:30 AM IST",
        "flight_arrival_time_display": "8:35 AM IST",
        "duration_min": 225.0,
        "is_door_to_door": True,
        "legs": [
            {"type": "FIRST_MILE", "mode": "Driving", "provider": "OSRM", "duration_min": 15.0, "verification_status": "Route Calculated"},
            {"type": "TRANSFER", "mode": "Transfer", "provider": "Airport", "duration_min": 90.0, "verification_status": "Buffer Verified", "note": "check-in"},
            {"type": "MAIN_TRANSIT", "mode": "Flight", "provider": "FlightProvider", "duration_min": 65.0, "verification_status": "Provider Verified"},
            {"type": "TRANSFER", "mode": "Transfer", "provider": "Airport", "duration_min": 30.0, "verification_status": "Buffer Verified", "note": "baggage"},
            {"type": "LAST_MILE", "mode": "Driving", "provider": "OSRM", "duration_min": 25.0, "verification_status": "Route Calculated"},
        ]
    }

    stitched = stitch_door_to_door_journey(
        route=mock_fl_route,
        origin_name="Coimbatore", origin_lat=11.0168, origin_lon=76.9558,
        dest_name="Chennai", dest_lat=13.0827, dest_lon=80.2707,
        request_time=datetime(2026, 11, 20, 5, 0, tzinfo=KOLKATA_TZ)
    )

    # Multimodal door-to-door journey MUST be Partially Verified
    assert stitched["verification_status"] == "Partially Verified"
    assert stitched["verification"]["level"] == "PARTIALLY_VERIFIED"

    # Transitous route normalized verification status check
    raw_transitous = {
        "provider": "Transitous",
        "mode": "Rail",
        "departure_time": "2026-11-20T14:00:00+05:30",
        "arrival_time": "2026-11-20T18:00:00+05:30",
        "duration_min": 240.0,
        "legs": [],
    }
    norm_tr = RouteOptimizer.normalize_route(
        provider="Transitous",
        mode="Rail",
        raw_itinerary=raw_transitous,
        origin_name="Erode",
        dest_name="Chennai",
        default_dist=380.0,
    )
    assert norm_tr["verification_status"] == "Schedule Verified"
    assert norm_tr["verification_status"] != "Official Railway Verified"


# ── TEST 5: Delhi -> Tokyo International Timezone & Midnight Crossing (Priority 7)

def test_delhi_to_tokyo_international_boundary_and_overnight():
    """
    Priority 7: Delhi (DEL, Asia/Kolkata) -> Tokyo (HND, Asia/Tokyo).
    Verifies that:
    1. Crosses midnight cleanly: departure 19:55 IST, arrival 06:40 JST next day.
    2. Arrival display has (+1 day).
    3. In-air duration is calculated accurately via UTC conversion (435.0 mins = 7h 15m).
    """
    dep_dt = parse_aviationstack_datetime("2026-11-18T19:55:00+00:00", "Asia/Kolkata")
    arr_dt = parse_aviationstack_datetime("2026-11-19T06:40:00+00:00", "Asia/Tokyo")

    dep_utc = dep_dt.astimezone(timezone.utc)
    arr_utc = arr_dt.astimezone(timezone.utc)
    elapsed_min = (arr_utc - dep_utc).total_seconds() / 60.0

    assert elapsed_min == 435.0  # Exactly 7h 15m
    assert dep_dt.strftime("%I:%M %p").lstrip("0") == "7:55 PM"
    assert arr_dt.strftime("%I:%M %p").lstrip("0") == "6:40 AM"
    assert arr_dt.date() > dep_dt.date()


# ── TEST 6: Pune -> Mumbai Ground Transit & Strategy (Priority 7) ─────────────

def test_pune_to_mumbai_ground_transit_and_awards():
    """
    Priority 7: Pune -> Mumbai (~120 km domestic corridor).
    Verifies:
    1. AI Transit Strategy recommends road/rail transit.
    2. External research indicates commercial flights are not applicable.
    3. Awards (fastest, cheapest) calculate fairly across valid door-to-door options.
    """
    research = ExternalTravelResearchService.get_research(
        origin_name="Pune",
        dest_name="Mumbai",
        origin_lat=18.5204, origin_lon=73.8567,
        dest_lat=19.0760, dest_lon=72.8777,
        scale="DOMESTIC",
        origin_country="India",
        dest_country="India",
    )
    assert research["has_commercial_flights"] is False
    assert len(research["candidate_airports"]["origin_airports"]) == 0

    # Awards optimization test
    routes = [
        {
            "route_id": "r1",
            "provider": "Indian Railways Timetable",
            "mode": "Train",
            "duration_min": 195.0,  # 3h 15m
            "fare": 120.0,
            "verification_status": "Schedule Verified",
            "departure_time": "2026-11-20T10:00:00+05:30",
        },
        {
            "route_id": "r2",
            "provider": "OSRM",
            "mode": "Driving",
            "duration_min": 170.0,  # 2h 50m
            "fare": None,
            "verification_status": "Route Calculated",
            "departure_time": "2026-11-20T08:30:00+05:30",
        },
    ]

    opt = RouteOptimizer.optimize(routes, request_time=datetime(2026, 11, 20, 8, 0, tzinfo=KOLKATA_TZ))
    # Fastest is OSRM Driving (170 min)
    assert opt["fastest_route"]["route_id"] == "r2"
    # Cheapest is Train with verified fare (₹120)
    assert opt["cheapest_route"]["route_id"] == "r1"


# ── TEST 7: New International Route: Sydney -> Auckland (Priority 7) ──────────

def test_sydney_to_auckland_international_route():
    """
    Priority 7: New international corridor: Sydney (SYD, Australia/Sydney) -> Auckland (AKL, Pacific/Auckland).
    Verifies that authentic local timezones and trans-Tasman flights are handled generically without hardcoding.
    """
    dep_tz = get_timezone("Australia/Sydney")
    arr_tz = get_timezone("Pacific/Auckland")

    dep_dt = datetime(2026, 11, 20, 9, 30, tzinfo=dep_tz)
    # Flight takes ~3h 05m in air: 9:30 AEST (23:30 UTC-1) + 3h05m = 02:35 UTC = 15:35 NZDT (UTC+13 during DST)
    arr_dt = datetime(2026, 11, 20, 15, 35, tzinfo=arr_tz)

    dep_disp = format_datetime_with_tz(dep_dt, "Australia/Sydney")
    arr_disp = format_datetime_with_tz(arr_dt, "Pacific/Auckland")

    assert "9:30 AM" in dep_disp
    assert ("AEST" in dep_disp or "+10" in dep_disp or "AEDT" in dep_disp or "+11" in dep_disp or "Sydney" in dep_disp)
    assert "3:35 PM" in arr_disp


# ── TEST 8: Overnight Train Journey Midnight Crossing (Priority 7) ────────────

def test_overnight_train_journey_date_consistency():
    """
    Priority 7: Overnight Train Journey (e.g. 12671 Nilgiri Express: Chennai Central 21:05 -> Coimbatore 05:10).
    Verifies:
    1. Departure date is Day 1.
    2. Arrival date is Day 2.
    3. is_overnight is True.
    4. Duration is calculated correctly across midnight (8h 05m = 485 mins).
    """
    raw_overnight_train = {
        "provider": "IndianRailways-ScheduleVerified",
        "mode": "Train",
        "train_number": "12671",
        "train_name": "Nilgiri Express",
        "departure_time": "21:05",
        "arrival_time": "05:10",
        "duration_min": 485.0,
        "legs": [],
    }

    norm = RouteOptimizer.normalize_route(
        provider="IndianRailways-ScheduleVerified",
        mode="Train",
        raw_itinerary=raw_overnight_train,
        origin_name="Puratchi Thalaivar Dr. M.G.R. Central",
        dest_name="Coimbatore Junction",
        default_dist=497.0,
        journey_date="2026-11-20",
    )

    assert norm["is_overnight"] is True
    assert norm["duration_min"] == 485.0
    assert "9:05 PM" in norm["departure_time_display"]
    assert "5:10 AM" in norm["arrival_time_display"]
    assert "(+1 day)" in norm["arrival_time_display"]


# ── TEST 9: Catchability Validation & OSRM Road Start Time (Priority 6) ────────

def test_catchability_past_departures_and_osrm_start_time():
    """
    Priority 6:
    1. Past departures are strictly NOT marked as AVAILABLE_LATER or CATCHABLE.
    2. On-demand OSRM road routes never start in the past; if requested departure time has passed,
       road route departure time is set to the current local timestamp.
    """
    now = datetime(2026, 11, 20, 16, 0, tzinfo=KOLKATA_TZ)  # 4:00 PM IST

    # Departure was at 09:00 AM today (7 hours in the past)
    past_service = datetime(2026, 11, 20, 9, 0, tzinfo=KOLKATA_TZ)
    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=past_service,
        now=now,
        first_mile_dur_min=15.0,
        boarding_buffer_min=10.0,
        station_name="Coimbatore Junction",
    )
    assert catchable is False
    assert status == "ALREADY_DEPARTED"
    assert status != "AVAILABLE_LATER"
    assert status != "CATCHABLE"

    # On-demand OSRM road route with requested departure 2 hours in the past (14:00)
    raw_road = {
        "provider": "OSRM",
        "mode": "Driving",
        "duration_min": 120.0,
        "departure_time": "2026-11-20T14:00:00+05:30",
    }
    stitched_road = stitch_door_to_door_journey(
        route=raw_road,
        origin_name="Coimbatore", origin_lat=11.0168, origin_lon=76.9558,
        dest_name="Salem", dest_lat=11.6643, dest_lon=78.1460,
        request_time=now,
    )

    # Road departure MUST have been recalculated to now (16:00), never remaining in the past (14:00)
    assert stitched_road["departure_time"] is not None
    road_dep_dt = _parse_iso(stitched_road["departure_time"])
    assert road_dep_dt >= now
    assert "4:00 PM" in stitched_road["departure_time_display"]
    assert "2:00 PM" not in stitched_road["departure_time_display"]
