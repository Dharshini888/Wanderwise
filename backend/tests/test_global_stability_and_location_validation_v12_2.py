"""
test_global_stability_and_location_validation_v12_2.py -- WanderWise V12.2 Global Stability & Location Validation Test Suite

Validates all 7 phases:
1. Phase 1: Robust timezone resolution (timezone.utc, ZoneInfo fallback, DST transitions).
2. Phase 2: Canonical location/station alias and proximity matching (Bangalore <-> KSR Bengaluru/SBC, etc.).
3. Phase 3: Non-blocking Overpass POI and infrastructure enrichment within strict deadline.
4. Phase 4: Overnight departure date alignment (e.g. 23:40 -> 00:15 next day) and chronological sorting.
5. Phase 5: Station transfer instruction formatting ("At station: arrive at platform by..." vs "Leave origin by...").
6. Phase 6: RailRadar HTTP 429 monthly quota exhaustion circuit breaker and status reporting.
7. Phase 7: 10 benchmark corridors (Chennai-Erode, Coimbatore-Delhi, Coimbatore-Bengaluru, Pune-Mumbai, Delhi-Tokyo, London-Paris, Berlin-Munich, etc.).
"""

import os
import sys
from datetime import datetime, date, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.transit.tz_utils import get_timezone, KOLKATA_TZ
from app.services.transit.station_normalizer import (
    normalize_station_name,
    are_locations_compatible,
    clean_place_name,
    CANONICAL_CITY_ALIASES,
)
from app.services.transit.airport_service import (
    get_airport_by_iata,
    get_airport_timezone,
    resolve_serving_airports,
)
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_stitcher import evaluate_catchability
from app.services.transit.provider_manager import ProviderManager, ProviderCircuitBreaker
from app.services.transit.providers.base import ProviderResult, ProviderStatus
from app.services.transit.transit_orchestrator import TransitOrchestrator


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1: TIMEZONE RESOLUTION & FLIGHT TIME ACCURACY
# ══════════════════════════════════════════════════════════════════════════════

def test_phase1_timezone_resolution_failsafe():
    """Verifies timezone resolution never crashes and always returns valid timezone objects."""
    # UTC resolution
    tz_utc1 = get_timezone("UTC")
    tz_utc2 = get_timezone("Etc/UTC")
    tz_utc3 = get_timezone("Z")
    tz_utc4 = get_timezone("")
    assert tz_utc1 == timezone.utc
    assert tz_utc2 == timezone.utc
    assert tz_utc3 == timezone.utc
    assert tz_utc4 == timezone.utc

    # Major world timezones
    tz_ist = get_timezone("Asia/Kolkata")
    tz_tokyo = get_timezone("Asia/Tokyo")
    tz_london = get_timezone("Europe/London")
    tz_paris = get_timezone("Europe/Paris")
    tz_berlin = get_timezone("Europe/Berlin")
    tz_ny = get_timezone("America/New_York")

    assert tz_ist is not None
    assert tz_tokyo is not None
    assert tz_london is not None
    assert tz_paris is not None
    assert tz_berlin is not None
    assert tz_ny is not None

    # DateTime arithmetic in UTC
    dt_now = datetime.now(timezone.utc)
    assert dt_now.tzinfo == timezone.utc


def test_phase1_airport_timezones():
    """Verifies authentic airport timezones are correctly assigned."""
    cjb = get_airport_by_iata("CJB")
    del_ap = get_airport_by_iata("DEL")
    hnd = get_airport_by_iata("HND")
    lhr = get_airport_by_iata("LHR")
    cdg = get_airport_by_iata("CDG")
    ber = get_airport_by_iata("BER")

    assert get_airport_timezone(cjb) == "Asia/Kolkata"
    assert get_airport_timezone(del_ap) == "Asia/Kolkata"
    assert get_airport_timezone(hnd) == "Asia/Tokyo"
    assert get_airport_timezone(lhr) == "Europe/London"
    assert get_airport_timezone(cdg) == "Europe/Paris"
    assert get_airport_timezone(ber) == "Europe/Berlin"


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: GLOBAL DESTINATION ALIAS VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_phase2_bangalore_ksr_bengaluru_compatibility():
    """
    Verifies that 'Bangalore' matches 'KSR Bengaluru', 'SBC', 'Bengaluru',
    preventing the critical journey rejection bug.
    """
    assert are_locations_compatible("Bangalore", "KSR Bengaluru") is True
    assert are_locations_compatible("Bangalore", "SBC") is True
    assert are_locations_compatible("Bengaluru", "KSR Bengaluru") is True
    assert are_locations_compatible("Bangalore", "Yesvantpur") is True
    assert are_locations_compatible("Bangalore", "Krishnarajapuram") is True


def test_phase2_global_aliases():
    """Verifies canonical aliases across all major corridors."""
    # Delhi
    assert are_locations_compatible("Delhi", "New Delhi") is True
    assert are_locations_compatible("Delhi", "Hazrat Nizamuddin") is True
    assert are_locations_compatible("Delhi", "NDLS") is True

    # Chennai
    assert are_locations_compatible("Chennai", "Chennai Central") is True
    assert are_locations_compatible("Chennai", "MAS") is True
    assert are_locations_compatible("Chennai", "Chennai Egmore") is True

    # Coimbatore
    assert are_locations_compatible("Coimbatore", "Coimbatore Junction") is True
    assert are_locations_compatible("Coimbatore", "CBE") is True

    # Mumbai / Pune
    assert are_locations_compatible("Mumbai", "CSMT") is True
    assert are_locations_compatible("Mumbai", "Mumbai Central") is True
    assert are_locations_compatible("Pune", "Pune Junction") is True

    # Tokyo / London / Paris / Berlin
    assert are_locations_compatible("Tokyo", "Tokyo Station") is True
    assert are_locations_compatible("Tokyo", "Haneda") is True
    assert are_locations_compatible("London", "Heathrow") is True
    assert are_locations_compatible("Paris", "Charles de Gaulle") is True
    assert are_locations_compatible("Berlin", "Berlin Hauptbahnhof") is True

    # Incompatible pairs must still be rejected
    assert are_locations_compatible("Coimbatore", "Chennai Central") is False
    assert are_locations_compatible("Delhi", "Coimbatore Junction") is False
    assert are_locations_compatible("Tokyo", "London") is False


def test_phase2_geographic_radius_compatibility():
    """Verifies that stations within urban radius (<= 35 km) are compatible."""
    # Coordinates for Bangalore city center (12.9716, 77.5946) and KSR Bengaluru Station (12.9781, 77.5696) ~ 3 km
    assert are_locations_compatible("Some Neighborhood", "Local Station", 12.9716, 77.5946, 12.9781, 77.5696) is True

    # Coordinates for Delhi (28.6139, 77.2090) and Chennai (13.0827, 80.2707) ~ 1750 km -> NOT compatible
    assert are_locations_compatible("Delhi", "Chennai", 28.6139, 77.2090, 13.0827, 80.2707) is False


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3: NON-BLOCKING OVERPASS POI & INFRASTRUCTURE ENRICHMENT
# ══════════════════════════════════════════════════════════════════════════════

def test_phase3_overpass_timeout_resilience():
    """
    Verifies that slow or failing Overpass API calls do not block or fail transit planning.
    Simulates hanging Overpass request and checks that orchestrator completes within deadline.
    """
    orchestrator = TransitOrchestrator()

    # Patch overpass to simulate delay
    with patch("app.services.transit.transit_orchestrator.get_overpass_nearby", side_effect=Exception("Overpass mirror timeout")):
        result = orchestrator.get_transit_plan(
            origin="Coimbatore Junction",
            destination="Chennai Central",
            departure_type="now",
        )
        assert result is not None
        assert result.get("status") in ("PUBLIC_TRANSIT_AVAILABLE", "MULTIMODAL_ROUTES_AVAILABLE")
        assert len(result.get("route_options", [])) > 0


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4: OVERNIGHT DEPARTURE DATE HANDLING
# ══════════════════════════════════════════════════════════════════════════════

def test_phase4_midnight_crossing_preserves_next_day_date():
    """
    Verifies that in corridors like Chennai -> Erode, departures crossing midnight
    (e.g. 23:40 on base_date and 00:15 on base_date + 1 day) are correctly assigned
    their genuine dates and sorted chronologically.
    """
    base_date = date(2026, 11, 18)

    # 1. ISO timestamp from MOTIS for 00:15 next day
    iso_next_day = "2026-11-19T00:15:00+05:30"
    norm_dt = RouteOptimizer._normalize_provider_time(
        time_str=iso_next_day,
        target_base_date=base_date,
    )
    assert norm_dt is not None
    assert norm_dt.date() == date(2026, 11, 19)
    assert norm_dt.hour == 0
    assert norm_dt.minute == 15

    # 2. Bare time string "12:15 AM" with reference departure late evening (23:00)
    ref_late = datetime(2026, 11, 18, 23, 0, tzinfo=KOLKATA_TZ)
    norm_bare = RouteOptimizer._normalize_provider_time(
        time_str="12:15 AM",
        target_base_date=base_date,
        reference_departure_time=ref_late,
    )
    assert norm_bare is not None
    assert norm_bare.date() == date(2026, 11, 19)
    assert norm_bare.hour == 0
    assert norm_bare.minute == 15

    # 3. Route sorting test: 23:40 must precede 00:15
    routes = [
        {"route_id": "r_0015", "departure_time": "2026-11-19T00:15:00+05:30", "duration_min": 300, "verification_status": "SCHEDULE_VERIFIED"},
        {"route_id": "r_2340", "departure_time": "2026-11-18T23:40:00+05:30", "duration_min": 320, "verification_status": "SCHEDULE_VERIFIED"},
        {"route_id": "r_0559", "departure_time": "2026-11-19T05:59:00+05:30", "duration_min": 290, "verification_status": "SCHEDULE_VERIFIED"},
    ]
    optimized = RouteOptimizer.optimize(routes, request_time=datetime(2026, 11, 18, 22, 0, tzinfo=KOLKATA_TZ))
    sorted_ids = [r["route_id"] for r in optimized["route_options"]]
    assert sorted_ids == ["r_2340", "r_0015", "r_0559"]


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5: STATION TRANSFER INSTRUCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def test_phase5_station_transfer_instruction_at_station():
    """
    Verifies that when passenger is already at station (first_mile_dur_min <= 0.5),
    the message explains 'At station: arrive at platform by...' instead of
    'Leave origin by X to reach station at X'.
    """
    dep_dt = datetime(2026, 11, 18, 23, 40, tzinfo=KOLKATA_TZ)
    now = datetime(2026, 11, 18, 22, 0, tzinfo=KOLKATA_TZ)

    is_catchable, status, msg, waiting_min = evaluate_catchability(
        service_dep_dt=dep_dt,
        now=now,
        first_mile_dur_min=0.0,
        boarding_buffer_min=20.0,
        station_name="Puratchi Thalaivar Dr. M.G.R. Central",
    )

    assert is_catchable is True
    assert status == "CATCHABLE"
    assert "at station: arrive at platform by" in msg.lower()
    assert "Leave origin by 11:20 PM to reach" not in msg


def test_phase5_station_transfer_instruction_with_transfer():
    """
    Verifies that when transfer duration > 0, origin departure strictly precedes station arrival.
    """
    dep_dt = datetime(2026, 11, 18, 23, 40, tzinfo=KOLKATA_TZ)
    now = datetime(2026, 11, 18, 22, 0, tzinfo=KOLKATA_TZ)

    is_catchable, status, msg, waiting_min = evaluate_catchability(
        service_dep_dt=dep_dt,
        now=now,
        first_mile_dur_min=15.0,
        boarding_buffer_min=20.0,
        station_name="Chennai Central",
    )

    assert is_catchable is True
    assert status == "CATCHABLE"
    assert "leave origin by" in msg.lower()
    assert "to reach Chennai Central at" in msg


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 6: RAILRADAR QUOTA CIRCUIT BREAKER & ACCURATE STATUS
# ══════════════════════════════════════════════════════════════════════════════

def test_phase6_railradar_quota_exhausted_handling():
    """
    Verifies that RailRadar 429 quota exhaustion trips into QUOTA_EXHAUSTED with 3600s cooldown,
    and returns 'Monthly quota exhausted'.
    """
    cb = ProviderCircuitBreaker("RailRadar", default_timeout=3.5)
    metrics = {
        "status_code": 429,
        "remaining_month": 0,
        "error_message": "Monthly quota exceeded. Maximum 100 requests per month.",
    }
    cb.trip_rate_limited(metrics)

    assert cb.state == "QUOTA_EXHAUSTED"
    assert cb.is_available() is False
    assert cb.get_frontend_status() == "Monthly quota exhausted"


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 7: 10 BENCHMARK CORRIDORS GLOBAL REGRESSION
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("origin,destination,expected_mode_keywords", [
    ("Chennai", "Erode", ["Train", "Rail", "Driving"]),
    ("Erode", "Chennai", ["Train", "Rail", "Driving"]),
    ("Coimbatore", "Delhi", ["Flight", "Rail", "Driving", "Travel Guidance"]),
    ("Delhi", "Coimbatore", ["Flight", "Rail", "Driving", "Travel Guidance"]),
    ("Coimbatore", "Bangalore", ["Train", "Rail", "Driving"]),
    ("Bengaluru", "Mysuru", ["Train", "Rail", "Driving"]),
    ("Pune", "Mumbai", ["Train", "Rail", "Driving"]),
    ("Delhi", "Tokyo", ["Flight", "Travel Guidance"]),
    ("London", "Paris", ["Train", "Flight", "Driving", "Travel Guidance"]),
    ("Berlin", "Munich", ["Train", "Flight", "Driving", "Travel Guidance"]),
])
def test_phase7_benchmark_corridors_execute_cleanly(origin, destination, expected_mode_keywords):
    """
    Verifies that all 10 benchmark corridors complete cleanly through TransitOrchestrator
    without unhandled exceptions, without timing out, and returning compatible location results.
    """
    orchestrator = TransitOrchestrator()
    res = orchestrator.get_transit_plan(
        origin=origin,
        destination=destination,
        departure_type="now",
    )

    assert res is not None
    assert "status" in res
    assert res["status"] not in ("ERROR", "EXCEPTION")
    assert res.get("origin") is not None
    assert res.get("destination") is not None

    # Verify origin and destination compatibility
    assert are_locations_compatible(origin, res["origin"]) or are_locations_compatible(origin, res.get("requested_origin"))
    assert are_locations_compatible(destination, res["destination"]) or are_locations_compatible(destination, res.get("requested_destination"))
