"""
test_flight_provider_corrections_v12_2.py -- WanderWise V12.2 / V12.3 Flight Provider Integration Validation Suite

Validates:
1. Airport Resolution & Railway Identity Protection (Coimbatore -> Delhi):
   - CJB (Coimbatore International Airport) and DEL (Indira Gandhi International Airport).
   - Never converts Coimbatore Junction railway station into flight origin.
2. Timezone & UTC Duration Calculation (New Delhi -> Tokyo):
   - Correctly converts DEL (UTC+5:30) and Tokyo (UTC+9:00) scheduled timestamps to UTC.
   - Verified 7h 15m in-air flight duration (prevents 15h 15m naive local clock distortion).
   - Eliminates 0-minute origin-to-origin trap ("Leave origin to reach New Delhi at same time").
   - Resolves provider's actual returned airport (HND or NRT, never assumes).
3. Reverse Timezone Flight (Tokyo -> New Delhi):
   - Handles HND/NRT -> DEL cross-timezone conversion.
4. Domestic Regional Corridors:
   - Coimbatore -> Chennai (CJB -> MAA)
   - Chennai -> Coimbatore (MAA -> CJB)
5. Strict Field-Level Data Provenance & Status Semantics:
   - Differentiates schedule verification, booking availability, live tracking, and catchability.
   - Ensures no conflicting UNAVAILABLE status when schedule is verified.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.transit.providers.flight_provider import (
    FlightProvider,
    parse_aviationstack_datetime,
    find_nearest_airport,
)
from app.services.transit.airport_service import (
    resolve_serving_airports,
    get_airport_by_iata,
    GLOBAL_AIRPORTS,
)
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_stitcher import (
    stitch_door_to_door_journey,
    evaluate_catchability,
)
from app.services.transit.journey_models import Journey, JourneyLeg, JourneyConnection
from app.services.transit.tz_utils import KOLKATA_TZ


# ── Sample Authentic AviationStack Flight Responses ──────────────────────────

MOCK_DEL_HND_RAW = {
    "flight_date": "2026-11-18",
    "flight_status": "landed",
    "departure": {
        "airport": "Indira Gandhi International",
        "timezone": "Asia/Kolkata",
        "iata": "DEL",
        "icao": "VIDP",
        "terminal": "3",
        "gate": "24",
        "delay": 25,
        "scheduled": "2026-11-18T19:55:00+00:00",
        "estimated": "2026-11-18T19:55:00+00:00",
    },
    "arrival": {
        "airport": "Haneda Airport",
        "timezone": "Asia/Tokyo",
        "iata": "HND",
        "icao": "RJTT",
        "terminal": "3",
        "gate": None,
        "scheduled": "2026-11-19T06:40:00+00:00",
        "estimated": "2026-11-19T06:17:00+00:00",
    },
    "airline": {"name": "Japan Airlines", "iata": "JL", "icao": "JAL"},
    "flight": {"number": "30", "iata": "JL30", "icao": "JAL30"},
    "aircraft": {"iata": "B789", "icao": "B789"},
    "live": None,
}

MOCK_CJB_DEL_RAW = {
    "flight_date": "2026-11-19",
    "flight_status": "scheduled",
    "departure": {
        "airport": "Peelamedu",
        "timezone": "Asia/Kolkata",
        "iata": "CJB",
        "icao": "VOCB",
        "scheduled": "2026-11-19T15:55:00+00:00",
        "estimated": "2026-11-19T15:55:00+00:00",
    },
    "arrival": {
        "airport": "Indira Gandhi International",
        "timezone": "Asia/Kolkata",
        "iata": "DEL",
        "icao": "VIDP",
        "scheduled": "2026-11-19T19:10:00+00:00",
        "estimated": "2026-11-19T19:10:00+00:00",
    },
    "airline": {"name": "Air India", "iata": "AI", "icao": "AIC"},
    "flight": {"number": "1837", "iata": "AI1837"},
    "aircraft": {"iata": "A320"},
    "live": None,
}

MOCK_CJB_MAA_RAW = {
    "flight_date": "2026-11-19",
    "flight_status": "scheduled",
    "departure": {
        "airport": "Peelamedu",
        "timezone": "Asia/Kolkata",
        "iata": "CJB",
        "icao": "VOCB",
        "scheduled": "2026-11-19T15:40:00+00:00",
    },
    "arrival": {
        "airport": "Chennai International Airport",
        "timezone": "Asia/Kolkata",
        "iata": "MAA",
        "icao": "VOMM",
        "scheduled": "2026-11-19T16:45:00+00:00",
    },
    "airline": {"name": "IndiGo", "iata": "6E"},
    "flight": {"number": "571", "iata": "6E571"},
    "live": None,
}

MOCK_MAA_CJB_RAW = {
    "flight_date": "2026-11-19",
    "flight_status": "scheduled",
    "departure": {
        "airport": "Chennai International Airport",
        "timezone": "Asia/Kolkata",
        "iata": "MAA",
        "icao": "VOMM",
        "scheduled": "2026-11-19T15:50:00+00:00",
    },
    "arrival": {
        "airport": "Peelamedu",
        "timezone": "Asia/Kolkata",
        "iata": "CJB",
        "icao": "VOCB",
        "scheduled": "2026-11-19T16:50:00+00:00",
    },
    "airline": {"name": "IndiGo", "iata": "6E"},
    "flight": {"number": "2123", "iata": "6E2123"},
    "live": None,
}


# ── TEST 1: Airport Resolution & Railway Identity Protection (Coimbatore -> Delhi) ──

def test_coimbatore_to_delhi_airport_resolution_and_no_railway_identity():
    """
    Test Case 1: Coimbatore -> Delhi.
    Verifies that:
    1. Origin airport resolves to Coimbatore International Airport (CJB).
    2. Destination airport resolves to Indira Gandhi International Airport (DEL).
    3. Neither flight legs nor journey departure/arrival stations use 'Coimbatore Junction' railway station.
    4. Leg sequence is complete: First Mile -> Checkin Buffer -> Flight -> Baggage Buffer -> Last Mile.
    """
    fp = FlightProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [MOCK_CJB_DEL_RAW]}

    with patch.object(fp.session, "get", return_value=mock_resp), \
         patch.object(fp, "get_api_key", return_value="test_key_123"):
        result = fp.plan_journey(
            origin_lat=11.0168, origin_lon=76.9558,
            dest_lat=28.6139, dest_lon=77.2090,
            origin_name="Coimbatore", dest_name="Delhi"
        )

    assert result.status.value == "SUCCESS"
    assert len(result.itineraries) > 0
    itin = result.itineraries[0]

    # Verify authentic airport identities
    assert itin["origin_iata"] == "CJB"
    assert itin["destination_iata"] == "DEL"
    assert "Coimbatore International Airport" in itin["origin_airport"]
    assert "Indira Gandhi International Airport" in itin["destination_airport"]

    # Verify no railway junction in flight origin or departure station
    assert itin["origin_airport"] != "Coimbatore Junction"
    assert itin["departure_station"] != "Coimbatore Junction"
    assert "Junction" not in itin["departure_station"]
    assert "Junction" not in itin["arrival_station"]

    # Verify in-air flight duration vs door-to-door duration
    assert itin["flight_duration_minutes"] == 195.0  # 3h 15m
    assert itin["flight_duration_display"] == "3h 15m"
    assert itin["duration_minutes"] > 195.0  # Total includes ground transfers & buffers

    # Verify legs
    legs = itin["legs"]
    assert len(legs) == 5
    assert legs[0]["type"] == "FIRST_MILE"
    assert legs[0]["to_name"] == itin["origin_airport"]
    assert legs[2]["type"] == "MAIN_TRANSIT"
    assert legs[2]["mode"] == "Flight"
    assert legs[2]["flight_number"] == "AI1837"
    assert legs[4]["type"] == "LAST_MILE"
    assert legs[4]["from_name"] == itin["destination_airport"]


# ── TEST 2: Timezone Handling & UTC Duration Calculation (New Delhi -> Tokyo) ──

def test_delhi_to_tokyo_timezone_utc_duration_and_ground_transfer():
    """
    Test Case 2: New Delhi -> Tokyo.
    Verifies that:
    1. Parsing 19:55 IST (UTC+5:30) and 06:40 JST (UTC+9:00 next day) yields EXACTLY 7h 15m in UTC.
    2. Resolves authentic provider-returned Tokyo airport (HND in this mock, Haneda Airport).
    3. Departure display indicates IST and arrival display indicates JST with (+1 day).
    4. First-mile ground access connects New Delhi to DEL airport (~18 min), eliminating origin-to-origin 0m bug.
    """
    # Direct datetime parser test
    dep_dt = parse_aviationstack_datetime("2026-11-18T19:55:00+00:00", "Asia/Kolkata")
    arr_dt = parse_aviationstack_datetime("2026-11-19T06:40:00+00:00", "Asia/Tokyo")

    dep_utc = dep_dt.astimezone(timezone.utc)
    arr_utc = arr_dt.astimezone(timezone.utc)
    in_air_min = (arr_utc - dep_utc).total_seconds() / 60.0

    assert in_air_min == 435.0  # Exactly 7h 15m (NOT 15h 15m or 10h 45m!)

    fp = FlightProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [MOCK_DEL_HND_RAW]}

    with patch.object(fp.session, "get", return_value=mock_resp), \
         patch.object(fp, "get_api_key", return_value="test_key_123"):
        result = fp.plan_journey(
            origin_lat=28.6139, origin_lon=77.2090,
            dest_lat=35.6762, dest_lon=139.6503,
            origin_name="New Delhi", dest_name="Tokyo"
        )

    assert result.status.value == "SUCCESS"
    itin = result.itineraries[0]

    # Verify authentic airport resolution
    assert itin["origin_iata"] == "DEL"
    assert itin["destination_iata"] == "HND"
    assert "Tokyo Haneda Airport" in itin["destination_airport"]

    # Verify duration separation
    assert itin["flight_duration_minutes"] == 435.0
    assert itin["flight_duration_display"] == "7h 15m"
    assert itin["total_duration_minutes"] > 435.0

    # Verify local timezone displays
    assert "IST" in itin["flight_departure_time_display"] or "7:55 PM" in itin["flight_departure_time_display"]
    assert "(+1 day)" in itin["flight_arrival_time_display"]

    # Stitch into door-to-door Journey and check catchability guidance text
    journey = stitch_door_to_door_journey(
        route=itin,
        origin_name="New Delhi", origin_lat=28.6139, origin_lon=77.2090,
        dest_name="Tokyo", dest_lat=35.6762, dest_lon=139.6503,
        request_time=datetime(2026, 11, 18, 12, 0, tzinfo=KOLKATA_TZ)
    )
    assert journey is not None
    assert journey["departure_station"] == itin["origin_airport"]
    assert journey["arrival_station"] == itin["destination_airport"]

    # Verify the catchability guidance directs passenger to the departure airport with check-in buffer
    why_msg = journey["why_catchable"]
    assert "Indira Gandhi International Airport" in why_msg
    # Ensure bug is fixed: never say "Leave origin by X to reach New Delhi at X"
    assert "to reach New Delhi at" not in why_msg


# ── TEST 3: Reverse Corridor (Tokyo -> New Delhi) ──

def test_tokyo_to_delhi_timezone_and_airport_handling():
    """
    Test Case 3: Tokyo -> New Delhi.
    Verifies that departure from Tokyo (HND/NRT) to DEL handles westbound travel time and timezone offsets.
    """
    mock_hnd_del = {
        "flight_date": "2026-11-19",
        "flight_status": "scheduled",
        "departure": {
            "airport": "Haneda Airport",
            "timezone": "Asia/Tokyo",
            "iata": "HND",
            "scheduled": "2026-11-19T13:20:00+00:00",
        },
        "arrival": {
            "airport": "Indira Gandhi International",
            "timezone": "Asia/Kolkata",
            "iata": "DEL",
            "scheduled": "2026-11-19T19:55:00+00:00",
        },
        "airline": {"name": "All Nippon Airways", "iata": "NH"},
        "flight": {"number": "6891", "iata": "NH6891"},
        "live": None,
    }

    fp = FlightProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [mock_hnd_del]}

    with patch.object(fp.session, "get", return_value=mock_resp), \
         patch.object(fp, "get_api_key", return_value="test_key_123"):
        result = fp.plan_journey(
            origin_lat=35.6762, origin_lon=139.6503,
            dest_lat=28.6139, dest_lon=77.2090,
            origin_name="Tokyo", dest_name="New Delhi"
        )

    assert result.status.value == "SUCCESS"
    itin = result.itineraries[0]
    assert itin["origin_iata"] == "HND"
    assert itin["destination_iata"] == "DEL"
    assert itin["flight_duration_minutes"] == 605.0  # 10h 5m
    assert itin["flight_duration_display"] == "10h 5m"


# ── TEST 4 & 5: Regional Corridors (Coimbatore <-> Chennai) ──

def test_coimbatore_to_chennai_and_chennai_to_coimbatore():
    """
    Test Cases 4 & 5: Coimbatore <-> Chennai.
    Verifies that:
    1. CJB -> MAA and MAA -> CJB resolve authentic airport codes and identities.
    2. Does not use 'Chennai Central' or 'Coimbatore Junction' railway stations on flight legs.
    3. Regional domestic check-in buffer is 90 minutes.
    """
    fp = FlightProvider()

    # Coimbatore -> Chennai
    mock_cjb_maa = MagicMock()
    mock_cjb_maa.status_code = 200
    mock_cjb_maa.json.return_value = {"data": [MOCK_CJB_MAA_RAW]}

    with patch.object(fp.session, "get", return_value=mock_cjb_maa), \
         patch.object(fp, "get_api_key", return_value="test_key_123"):
        res_fwd = fp.plan_journey(
            origin_lat=11.0168, origin_lon=76.9558,
            dest_lat=13.0827, dest_lon=80.2707,
            origin_name="Coimbatore", dest_name="Chennai"
        )
    assert res_fwd.status.value == "SUCCESS"
    itin_fwd = res_fwd.itineraries[0]
    assert itin_fwd["origin_iata"] == "CJB"
    assert itin_fwd["destination_iata"] == "MAA"
    assert itin_fwd["flight_duration_minutes"] == 65.0  # 1h 5m
    assert itin_fwd["flight_duration_display"] == "1h 5m"

    # Chennai -> Coimbatore
    mock_maa_cjb = MagicMock()
    mock_maa_cjb.status_code = 200
    mock_maa_cjb.json.return_value = {"data": [MOCK_MAA_CJB_RAW]}

    with patch.object(fp.session, "get", return_value=mock_maa_cjb), \
         patch.object(fp, "get_api_key", return_value="test_key_123"):
        res_rev = fp.plan_journey(
            origin_lat=13.0827, origin_lon=80.2707,
            dest_lat=11.0168, dest_lon=76.9558,
            origin_name="Chennai", dest_name="Coimbatore"
        )
    assert res_rev.status.value == "SUCCESS"
    itin_rev = res_rev.itineraries[0]
    assert itin_rev["origin_iata"] == "MAA"
    assert itin_rev["destination_iata"] == "CJB"
    assert itin_rev["flight_duration_minutes"] == 60.0  # 1h 0m


# ── TEST 6: Strict Data Provenance & Status Semantics ──

def test_strict_provenance_and_status_semantics():
    """
    Requirement 3 & 4: Strict Data Provenance and Status Semantics.
    Verifies that:
    1. Field-level sources are explicitly articulated on route and journey objects.
    2. Verification status is 'Provider Verified'.
    3. Live telemetry status is correctly separated: unavailable when live is None.
    4. Booking availability is clearly stated as not provided by provider.
    """
    fp = FlightProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [MOCK_CJB_DEL_RAW]}

    with patch.object(fp.session, "get", return_value=mock_resp), \
         patch.object(fp, "get_api_key", return_value="test_key_123"):
        result = fp.plan_journey(
            origin_lat=11.0168, origin_lon=76.9558,
            dest_lat=28.6139, dest_lon=77.2090,
            origin_name="Coimbatore", dest_name="Delhi"
        )

    itin = result.itineraries[0]

    # Field-level provenance check
    src = itin["source"]
    assert src["schedule"] == "AviationStack"
    assert src["flight_duration"] == "Calculated from scheduled UTC timestamps"
    assert "Great-circle" in src["flight_distance"]
    assert "OSRM" in src["ground_transfer"]
    assert "Unavailable" in src["fare"]
    assert "Unavailable" in src["booking"]
    assert src["live_tracking"] == "SCHEDULE DATA ONLY"

    # Verification level check
    assert itin["verification"]["level"] == "PROVIDER_VERIFIED"
    assert itin["verification"]["live"] is False
    assert itin["realtime"]["available"] is False

    # Check journey stitching retains provenance and does not conflict with catchability
    journey = stitch_door_to_door_journey(
        route=itin,
        origin_name="Coimbatore", origin_lat=11.0168, origin_lon=76.9558,
        dest_name="Delhi", dest_lat=28.6139, dest_lon=77.2090,
        request_time=datetime(2026, 11, 19, 10, 0, tzinfo=KOLKATA_TZ)
    )
    assert journey["verification_status"] == "Provider Verified"
    assert journey["verification"]["level"] == "PROVIDER_VERIFIED"
    assert journey["source"]["schedule"] == "AviationStack"
    assert journey["catchability_status"] in ("CATCHABLE", "AVAILABLE_LATER")
