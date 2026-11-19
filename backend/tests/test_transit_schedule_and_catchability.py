"""
test_transit_schedule_and_catchability.py -- WanderWise V12.2 Schedule, Date & Catchability Regression Suite

Tests:
1. Exact catchability classification for CBE -> SBC at 10:53 PM (5m buffer):
   - 8:50 AM today -> ALREADY_DEPARTED
   - 10:45 PM today -> CANNOT_CATCH
   - 11:05 PM today -> CATCHABLE
   - 8:50 AM tomorrow -> CATCHABLE
2. First-mile access affects catchability
3. Midnight crossing date increment and positive duration
4. Timezone-aware vs naive timestamp comparison
5. Missing or invalid timestamps handling
6. OSRM driving classification (never train)
7. Time consistency between normalized route and stitched journey
8. Duplicate journeys deduplication
9. Ranking excludes already-departed services
10. End-to-end CBE to SBC transit plan with scheduled timestamps
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime, timedelta, timezone, date

from app.services.transit.journey_stitcher import (
    evaluate_catchability,
    stitch_door_to_door_journey,
    stitch_all_journeys,
    _format_time_display,
)
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.journey_models import Journey, JourneyLeg, JourneyConnection
from app.services.transit.transit_orchestrator import TransitOrchestrator


def test_catchability_four_departures_cbe_to_sbc():
    """
    User scenario:
    - Origin: Coimbatore Junction
    - Destination: KSR Bengaluru
    - Current time: 10:53 PM (22:53)
    - Boarding buffer: 5 minutes
    - First mile: 0 mins (already at station)
    - Earliest boarding time: 10:58 PM (22:58)

    Target departures:
    1. 8:50 AM today -> ALREADY DEPARTED
    2. 10:45 PM today -> CANNOT CATCH (8 mins ago, departs before 10:58 PM)
    3. 11:05 PM today -> CATCHABLE (departs after 10:58 PM)
    4. 8:50 AM tomorrow -> CATCHABLE (future date)
    """
    now = datetime(2026, 11, 17, 22, 53, 0)

    # 1. 8:50 AM today (08:50) -> ALREADY DEPARTED (> 15m ago today)
    dep_850_today = datetime(2026, 11, 17, 8, 50, 0)
    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=dep_850_today,
        now=now,
        first_mile_dur_min=0.0,
        boarding_buffer_min=5.0,
        station_name="Coimbatore Junction",
    )
    assert not catchable
    assert status == "ALREADY_DEPARTED"
    assert "Already departed" in reason
    assert wait == 0.0

    # 2. 10:45 PM today (22:45) -> CANNOT CATCH (departed 8m ago, before earliest boarding 22:58)
    dep_1045_today = datetime(2026, 11, 17, 22, 45, 0)
    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=dep_1045_today,
        now=now,
        first_mile_dur_min=0.0,
        boarding_buffer_min=5.0,
        station_name="Coimbatore Junction",
    )
    assert not catchable
    assert status == "CANNOT_CATCH"
    assert "Cannot catch" in reason
    assert wait == 0.0

    # 3. 11:05 PM today (23:05) -> CATCHABLE (12 mins buffer available)
    dep_1105_today = datetime(2026, 11, 17, 23, 5, 0)
    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=dep_1105_today,
        now=now,
        first_mile_dur_min=0.0,
        boarding_buffer_min=5.0,
        station_name="Coimbatore Junction",
    )
    assert catchable
    assert status == "CATCHABLE"
    assert wait == 12.0  # 23:05 - 22:53 = 12 mins
    assert "Catchable" in reason or "buffer" in reason

    # 4. 8:50 AM tomorrow (08:50 Nov 18) -> CATCHABLE (tomorrow morning)
    dep_850_tomorrow = datetime(2026, 11, 18, 8, 50, 0)
    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=dep_850_tomorrow,
        now=now,
        first_mile_dur_min=0.0,
        boarding_buffer_min=5.0,
        station_name="Coimbatore Junction",
    )
    assert catchable
    assert status in ("CATCHABLE", "AVAILABLE_LATER")
    assert wait > 0
    assert "tomorrow" in reason.lower()


def test_first_mile_access_impacts_catchability():
    """
    If the user is 15 mins away from Coimbatore Junction:
    - now = 10:53 PM
    - first mile = 15 mins -> station arrival 11:08 PM
    - buffer = 5 mins -> minimum boarding time 11:13 PM
    - 11:05 PM train departs before 11:13 PM -> CANNOT CATCH
    """
    now = datetime(2026, 11, 17, 22, 53, 0)
    dep_1105 = datetime(2026, 11, 17, 23, 5, 0)

    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=dep_1105,
        now=now,
        first_mile_dur_min=15.0,
        boarding_buffer_min=5.0,
        station_name="Coimbatore Junction",
    )
    assert not catchable
    assert status == "CANNOT_CATCH"
    assert "11:13 PM" in reason


def test_midnight_crossing_journey():
    """
    Train departing at 11:30 PM and arriving at 4:30 AM next day:
    - Must automatically increment arrival date by 1 day.
    - Duration must be positive (300 minutes, 5 hours).
    - Display string must append (+1 day).
    """
    raw_itinerary = {
        "provider": "RailRadar",
        "mode": "Train",
        "departure_time": "11:30 PM",
        "arrival_time": "04:30 AM",
        "departure_station": "Coimbatore Junction",
        "arrival_station": "KSR Bengaluru",
        "distance_km": 378.0,
        "legs": [],
    }
    target_date = date(2026, 11, 17)
    norm = RouteOptimizer.normalize_route(
        provider="RailRadar",
        mode="Train",
        raw_itinerary=raw_itinerary,
        origin_name="Coimbatore Junction",
        dest_name="KSR Bengaluru",
        default_dist=378.0,
        journey_date="2026-11-17",
    )
    assert norm is not None
    assert norm["is_overnight"] is True
    assert norm["duration_min"] == 300.0  # 5 hours
    assert "(+1 day)" in norm["arrival_time_display"]
    dep_dt = datetime.fromisoformat(norm["departure_time"])
    arr_dt = datetime.fromisoformat(norm["arrival_time"])
    assert arr_dt > dep_dt
    assert (arr_dt.date() - dep_dt.date()).days == 1


def test_timezone_aware_and_naive_comparison():
    """
    Comparing timezone-aware (IST +05:30) with naive datetime must not throw TypeError.
    """
    tz_ist = timezone(timedelta(hours=5, minutes=30))
    now_naive = datetime(2026, 11, 17, 22, 53, 0)
    dep_aware = datetime(2026, 11, 17, 23, 5, 0, tzinfo=tz_ist)

    # Must execute cleanly without exception
    catchable, status, reason, wait = evaluate_catchability(
        service_dep_dt=dep_aware,
        now=now_naive,
        first_mile_dur_min=0.0,
        boarding_buffer_min=5.0,
        station_name="Coimbatore Junction",
    )
    assert catchable
    assert status == "CATCHABLE"


def test_missing_and_invalid_timestamps():
    """
    Missing or malformed timestamps must return SCHEDULE_UNAVAILABLE gracefully.
    """
    now = datetime(2026, 11, 17, 22, 53, 0)

    # None
    c1, s1, r1, w1 = evaluate_catchability(None, now)
    assert s1 == "SCHEDULE_UNAVAILABLE"
    assert c1 is True  # does not hard-block when schedule unverified

    # Malformed route itinerary
    raw_bad = {
        "provider": "RailRadar",
        "departure_time": "InvalidTimeStr",
        "arrival_time": "None",
        "duration_min": None,
    }
    norm = RouteOptimizer.normalize_route(
        provider="RailRadar",
        mode="Train",
        raw_itinerary=raw_bad,
        origin_name="Station A",
        dest_name="Station B",
        default_dist=100.0,
    )
    assert norm is not None
    assert norm["duration_min"] >= 1.0


def test_osrm_classification_is_driving_not_train():
    """
    OSRM road route must be categorized strictly as Driving / Road, never Train.
    """
    raw_osrm = {
        "provider": "OSRM",
        "mode": "Driving",
        "duration_min": 272.8,
        "distance_km": 365.2,
        "geometry": [[11.0, 76.9], [12.9, 77.5]],
    }
    now = datetime(2026, 11, 17, 22, 53, 0)
    norm = RouteOptimizer.normalize_route(
        provider="OSRM",
        mode="Driving",
        raw_itinerary=raw_osrm,
        origin_name="Coimbatore",
        dest_name="Bengaluru",
        default_dist=365.0,
        departure_time=now,
    )
    assert norm["mode"] == "Driving"
    assert norm["provider"] == "OSRM"
    assert norm["verification_status"] == "Route Calculated"
    assert "train" not in norm["mode"].lower()


def test_time_consistency_card_vs_detailed_view():
    """
    Verifies that fractional duration (e.g. 272.8 minutes) produces identical
    departure and arrival times between the normalized route and the stitched journey.
    Eliminates the 3:25 AM vs 3:26 AM discrepancy.
    """
    now = datetime(2026, 11, 17, 22, 53, 0)
    raw_osrm = {
        "provider": "OSRM",
        "mode": "Driving",
        "duration_min": 272.8,
        "distance_km": 365.2,
        "geometry": [[11.0016, 76.9628], [12.9784, 77.5684]],
    }
    norm = RouteOptimizer.normalize_route(
        provider="OSRM",
        mode="Driving",
        raw_itinerary=raw_osrm,
        origin_name="Coimbatore Junction",
        dest_name="KSR Bengaluru",
        default_dist=365.2,
        departure_time=now,
    )
    stitched = stitch_door_to_door_journey(
        route=norm,
        origin_name="Coimbatore Junction",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_name="KSR Bengaluru",
        dest_lat=12.9784,
        dest_lon=77.5684,
        request_time=now,
    )
    # Both must match exactly down to the minute
    assert norm["departure_time_display"] == stitched["departure_time_display"]
    assert norm["arrival_time_display"] == stitched["arrival_time_display"]
    # Verify exact minute calculation: 22:53 + 273 mins = 03:26 AM (+1 day)
    assert stitched["arrival_time_display"] == "3:26 AM (+1 day)"
    assert norm["arrival_time_display"] == "3:26 AM (+1 day)"


def test_duplicate_journeys_deduplication():
    """
    stitch_all_journeys must eliminate duplicate journeys with the same train number
    or identical provider schedule.
    """
    now = datetime(2026, 11, 17, 22, 53, 0)
    route1 = {
        "route_id": "r1",
        "provider": "RailRadar",
        "mode": "Train",
        "train_number": "16525",
        "train_name": "Island Express",
        "departure_time": "2026-11-17T23:05:00",
        "arrival_time": "2026-11-18T06:40:00",
        "departure_station": "Coimbatore Junction",
        "arrival_station": "KSR Bengaluru",
        "duration_min": 455.0,
        "distance_km": 378.0,
    }
    # Duplicate with different route_id
    route2 = {
        "route_id": "r2",
        "provider": "RailRadar",
        "mode": "Train",
        "train_number": "16525",
        "train_name": "Island Express",
        "departure_time": "2026-11-17T23:05:00",
        "arrival_time": "2026-11-18T06:40:00",
        "departure_station": "Coimbatore Junction",
        "arrival_station": "KSR Bengaluru",
        "duration_min": 455.0,
        "distance_km": 378.0,
    }
    results = stitch_all_journeys(
        candidate_routes=[route1, route2],
        origin_name="Coimbatore Junction",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_name="KSR Bengaluru",
        dest_lat=12.9784,
        dest_lon=77.5684,
        request_time=now,
    )
    assert len(results) == 1
    assert results[0]["train_number"] == "16525"


def test_ranking_excludes_already_departed():
    """
    RouteOptimizer.optimize must not recommend an ALREADY_DEPARTED service
    as Best Overall or Fastest when catchable routes exist.
    """
    now = datetime(2026, 11, 17, 22, 53, 0)

    # Train departed at 8:50 AM (360 min) -> fastest on paper, but already departed!
    r_departed = {
        "route_id": "r_dep",
        "provider": "RailRadar",
        "mode": "Train",
        "departure_time": "2026-11-17T08:50:00",
        "arrival_time": "2026-11-17T14:50:00",
        "duration_min": 360.0,
        "distance_km": 378.0,
        "verification_status": "Provider Verified",
    }
    # Train departing at 11:05 PM (455 min) -> catchable!
    r_catchable = {
        "route_id": "r_cat",
        "provider": "RailRadar",
        "mode": "Train",
        "departure_time": "2026-11-17T23:05:00",
        "arrival_time": "2026-11-18T06:40:00",
        "duration_min": 455.0,
        "distance_km": 378.0,
        "verification_status": "Provider Verified",
    }

    optimized = RouteOptimizer.optimize([r_departed, r_catchable], request_time=now)
    assert optimized["best_overall_route"]["route_id"] == "r_cat"
    assert optimized["fastest_route"]["route_id"] == "r_cat"


def test_cbe_to_sbc_end_to_end_journey_times():
    """
    Tests end-to-end CBE to SBC planning at 10:53 PM:
    - Trains 16614 (10:45 PM) and 16525 (11:05 PM) are tested.
    - 16614 is CANNOT_CATCH.
    - 16525 is CATCHABLE.
    - Scheduled departure and arrival timestamps are strictly preserved on the journey card.
    """
    now = datetime(2026, 11, 17, 22, 53, 0)
    result = TransitOrchestrator.get_transit_plan(
        origin="Coimbatore Junction",
        destination="KSR Bengaluru",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_lat=12.9784,
        dest_lon=77.5684,
        departure_time=now.isoformat(),
        date="Today",
    )
    assert result is not None
    journeys = result.get("journeys", [])
    assert len(journeys) > 0

    # Find train 16525 (Island Express)
    island_exp = next((j for j in journeys if j.get("train_number") == "16525"), None)
    if island_exp:
        assert island_exp["catchability_status"] == "CATCHABLE"
        assert island_exp["catchable"] is True
        # Timestamps must reflect train schedule (11:05 PM -> 6:40 AM), NOT current time (10:53 PM)
        assert "11:05 PM" in island_exp["departure_time_display"]
        assert "6:40 AM" in island_exp["arrival_time_display"]

    # Find train 16614 (Rajkot Express, 10:45 PM)
    rajkot_exp = next((j for j in journeys if j.get("train_number") == "16614"), None)
    if rajkot_exp:
        assert rajkot_exp["catchability_status"] == "CANNOT_CATCH"
        assert rajkot_exp["catchable"] is False
        assert "10:45 PM" in rajkot_exp["departure_time_display"]
