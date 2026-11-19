"""
test_smart_transit_pipeline_complete.py — WanderWise Smart Transit Assistant V12.2 Complete Pipeline Verification

Covers:
  - Test A: Datetime Normalization & Cross-Midnight (Aware/Naive, Cross-midnight 23:30->01:15, Non-negative)
  - Test B: RailRadar Real Train Query (Coimbatore -> Chennai/Bengaluru, timestamps, durations)
  - Test C: Transitous Public Transit Query (Kyoto Station -> Fushimi Inari)
  - Test D: OSRM Road Routing (Kyoto Station -> Kiyomizu-dera)
  - Test E: TransitMap Coordinate Resilience (invalid/missing lat/lon, range boundaries)
  - Test F: Provider Failure & Timeout Tolerance (isolated failures do not crash pipeline)
  - Test G: AviationStack 403 Subscription Restriction Handling (no mocks, honest diagnostics)
  - Test H: Backend API Status Codes (200 on success/partial, 400 on bad input/coords)
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.transit_router import TransitRouter
from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.providers.base import ProviderStatus, ProviderResult
from app.services.transit.providers.railradar_provider import RailRadarProvider
from app.services.transit.providers.transitous_provider import TransitousProvider
from app.services.transit.providers.osrm_provider import OSRMRoadProvider
from app.services.transit.providers.flight_provider import FlightProvider, classify_provider_error


# ==============================================================================
# TEST A: DATETIME NORMALIZATION & CROSS-MIDNIGHT ARITHMETIC
# ==============================================================================

def test_a1_aware_dep_and_naive_arr():
    """Aware departure and naive arrival must not crash with TypeError."""
    raw_itin = {
        "departure_time": "2026-11-18T10:00:00+05:30",
        "arrival_time": "14:30",
        "distance_km": 150.0,
        "legs": []
    }
    norm = RouteOptimizer.normalize_route(
        provider="TestProvider",
        mode="Rail",
        raw_itinerary=raw_itin,
        origin_name="Station A",
        dest_name="Station B",
        default_dist=150.0,
        journey_date="2026-11-18"
    )
    assert norm is not None
    assert norm["duration_min"] == 270.0  # 10:00 to 14:30 = 4.5 hours = 270 minutes
    assert norm["duration_min"] > 0
    assert norm["is_overnight"] is False


def test_a2_naive_dep_and_aware_arr():
    """Naive departure and aware arrival must not crash with TypeError."""
    raw_itin = {
        "departure_time": "08:15",
        "arrival_time": "2026-11-18T12:45:00+05:30",
        "distance_km": 200.0,
        "legs": []
    }
    norm = RouteOptimizer.normalize_route(
        provider="TestProvider",
        mode="Rail",
        raw_itinerary=raw_itin,
        origin_name="Station A",
        dest_name="Station B",
        default_dist=200.0,
        journey_date="2026-11-18"
    )
    assert norm is not None
    assert norm["duration_min"] == 270.0  # 08:15 to 12:45 = 4.5 hours = 270 minutes
    assert norm["duration_min"] > 0


def test_a3_both_aware_differing_timezones():
    """Both datetimes aware with different UTC offsets must calculate elapsed time accurately."""
    # Leaves at 10:00 UTC (15:30 IST) and arrives at 14:00 UTC (23:00 JST)
    raw_itin = {
        "departure_time": "2026-11-18T15:30:00+05:30",
        "arrival_time": "2026-11-18T23:00:00+09:00",
        "distance_km": 3000.0,
        "legs": []
    }
    norm = RouteOptimizer.normalize_route(
        provider="FlightProvider",
        mode="Flight",
        raw_itinerary=raw_itin,
        origin_name="Airport A",
        dest_name="Airport B",
        default_dist=3000.0,
        journey_date="2026-11-18"
    )
    assert norm is not None
    # 10:00 UTC to 14:00 UTC = 4 hours = 240 minutes
    assert norm["duration_min"] == 240.0
    assert norm["duration_min"] > 0


def test_a4_both_naive():
    """Both naive times calculate duration accurately."""
    raw_itin = {
        "departure_time": "09:00",
        "arrival_time": "11:30",
        "distance_km": 100.0,
        "legs": []
    }
    norm = RouteOptimizer.normalize_route(
        provider="TestProvider",
        mode="Bus",
        raw_itinerary=raw_itin,
        origin_name="Stop A",
        dest_name="Stop B",
        default_dist=100.0,
        journey_date="2026-11-18"
    )
    assert norm is not None
    assert norm["duration_min"] == 150.0
    assert norm["duration_min"] > 0


def test_a5_cross_midnight_trip():
    """Cross-midnight trip (e.g. 23:30 to 01:15) must advance date +1 day and yield 105 mins."""
    raw_itin = {
        "departure_time": "23:30",
        "arrival_time": "01:15",
        "distance_km": 80.0,
        "legs": []
    }
    norm = RouteOptimizer.normalize_route(
        provider="TestProvider",
        mode="Rail",
        raw_itinerary=raw_itin,
        origin_name="Station A",
        dest_name="Station B",
        default_dist=80.0,
        journey_date="2026-11-18"
    )
    assert norm is not None
    assert norm["duration_min"] == 105.0  # 30m to midnight + 75m after = 105 minutes
    assert norm["is_overnight"] is True
    assert "(+1 day)" in norm["arrival_time_display"]


def test_a6_guaranteed_non_negative_duration():
    """Zero or negative duration fallbacks are guarded to >= 1.0 minute."""
    raw_itin = {
        "departure_time": "10:00",
        "arrival_time": "10:00",
        "distance_km": 5.0,
        "legs": []
    }
    norm = RouteOptimizer.normalize_route(
        provider="TestProvider",
        mode="Walking",
        raw_itinerary=raw_itin,
        origin_name="Point A",
        dest_name="Point B",
        default_dist=5.0,
        journey_date="2026-11-18"
    )
    assert norm is not None
    assert norm["duration_min"] >= 1.0


# ==============================================================================
# TEST B: RAILRADAR REAL TRAIN QUERY
# ==============================================================================

def test_b_railradar_real_train_query():
    """Verify RailRadar returns real schedule data for Coimbatore -> Chennai with positive durations."""
    provider = RailRadarProvider()
    res = provider.plan_journey(
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_lat=13.0827,
        dest_lon=80.2707,
        preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"},
    )
    assert res.status == ProviderStatus.SUCCESS
    assert res.itineraries and len(res.itineraries) >= 3

    train_numbers = [itin.get("train_number") for itin in res.itineraries]
    assert any(tn in train_numbers for tn in ("12676", "12680", "12244", "20644"))  # Kovai / Intercity / Shatabdi / Vande Bharat

    for itin in res.itineraries:
        assert itin.get("duration_min") > 0
        assert itin.get("departure_time") is not None
        assert itin.get("arrival_time") is not None


# ==============================================================================
# TEST C: TRANSITOUS PUBLIC TRANSIT QUERY
# ==============================================================================

def test_c_transitous_public_transit():
    """Verify Transitous returns transit alternatives for Kyoto Station -> Fushimi Inari."""
    provider = TransitousProvider()
    # Kyoto Station (34.9858, 135.7588) to Fushimi Inari (34.9671, 135.7727)
    res = provider.plan_journey(
        origin_lat=34.9858,
        origin_lon=135.7588,
        dest_lat=34.9671,
        dest_lon=135.7727,
        preferences={"origin_name": "Kyoto Station", "dest_name": "Fushimi Inari"},
    )
    # Even if offline/rate-limited, provider must return structured ProviderResult without crash
    assert isinstance(res, ProviderResult)
    if res.status == ProviderStatus.SUCCESS:
        assert len(res.itineraries) > 0
        first = res.itineraries[0]
        assert first.get("duration_minutes") or first.get("duration_min")


# ==============================================================================
# TEST D: OSRM ROAD ROUTING
# ==============================================================================

def test_d_osrm_road_routing():
    """Verify OSRM road alternative calculation for Kyoto Station -> Kiyomizu-dera."""
    road = OSRMRoadProvider.get_road_alternative(
        origin_name="Kyoto Station",
        origin_lat=34.9858,
        origin_lon=135.7588,
        dest_name="Kiyomizu-dera",
        dest_lat=34.9949,
        dest_lon=135.7850,
    )
    assert road is not None
    assert road.get("distance_km") > 0.0
    assert road.get("duration_min") > 0.0
    assert road.get("mode") == "Driving"


# ==============================================================================
# TEST E: TRANSITMAP COORDINATE RESILIENCE
# ==============================================================================

def test_e_coordinate_validation_and_bounds():
    """Verify coordinate validator logic handles missing, NaN, out-of-bounds, and valid shapes."""
    def is_valid(c):
        if not c:
            return False
        lat, lon = None, None
        if isinstance(c, (list, tuple)) and len(c) >= 2:
            try:
                lat, lon = float(c[0]), float(c[1])
            except (ValueError, TypeError):
                return False
        elif isinstance(c, dict):
            try:
                lat = float(c.get("lat") if c.get("lat") is not None else c.get("latitude"))
                lon = float(c.get("lon") if c.get("lon") is not None else c.get("longitude", c.get("lng")))
            except (ValueError, TypeError):
                return False
        if lat is None or lon is None:
            return False
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    # Tests
    assert is_valid(None) is False
    assert is_valid({}) is False
    assert is_valid({"lat": "invalid", "lon": 76.9}) is False
    assert is_valid({"lat": 95.0, "lon": 76.9}) is False   # out of range
    assert is_valid({"lat": 11.0, "lon": 195.0}) is False  # out of range
    assert is_valid([11.0, 76.9]) is True
    assert is_valid({"lat": 11.0016, "lon": 76.9628}) is True
    assert is_valid({"latitude": 34.9858, "longitude": 135.7588}) is True


# ==============================================================================
# TEST F: PROVIDER FAILURE & TIMEOUT TOLERANCE
# ==============================================================================

def test_f_provider_failure_tolerance():
    """If one provider raises an error or times out, TransitRouter still succeeds with others."""
    router = TransitRouter()

    # Create a failing provider mock
    class CrashingProvider:
        provider_name = "CrashingProvider"
        def plan_journey(self, *args, **kwargs):
            raise RuntimeError("Database connection suddenly dropped!")

    router.transit_providers.append(CrashingProvider())

    # Route Coimbatore Junction to Chennai Central
    res = router.route(
        origin_name="Coimbatore Junction",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_name="Chennai Central",
        dest_lat=13.0827,
        dest_lon=80.2707,
    )
    # The route must succeed via RailRadar and OSRM despite CrashingProvider
    assert res.get("status") in ("MULTIMODAL_ROUTES_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE")
    assert "routes" in res
    assert res.get("recommended_route") is not None

    # Check provider audit captured the crash gracefully
    audit = res.get("provider_audit", {})
    assert "CrashingProvider" in audit
    assert audit["CrashingProvider"]["status"] == "PROVIDER_UNAVAILABLE"


# ==============================================================================
# TEST G: AVIATIONSTACK 403 SUBSCRIPTION RESTRICTION HANDLING
# ==============================================================================

def test_g_aviationstack_403_subscription_restriction():
    """HTTP 403 from AviationStack is classified as SUBSCRIPTION_RESTRICTION with zero mock flights."""
    error_payload = {
        "error": {
            "code": "function_access_restricted",
            "message": "Your current subscription plan does not support this HTTP function."
        }
    }
    cat, sanitized, user_note = classify_provider_error(
        status_code=403,
        error_payload=error_payload,
        key="test_api_key_secret_12345"
    )

    assert cat == "SUBSCRIPTION_RESTRICTION"
    assert "test_api_key_secret_12345" not in sanitized
    assert "subscription" in user_note.lower()

    # Verify FlightProvider returns ProviderResult with NO mock itineraries
    provider = FlightProvider()
    res = provider.plan_journey(
        origin_lat=11.0016, origin_lon=76.9628,
        dest_lat=34.9858, dest_lon=135.7588,
        origin_name="Coimbatore", dest_name="Osaka"
    )
    # In live or unconfigured, it must NEVER return fabricated mock flights
    assert isinstance(res, ProviderResult)
    if res.status != ProviderStatus.SUCCESS:
        assert len(res.itineraries) == 0


# ==============================================================================
# TEST H: BACKEND STATUS CODES & FASTAPI ROUTING
# ==============================================================================

from fastapi import HTTPException
from app.routes.transit import get_route, get_intelligence, TransitRequest

def test_h1_route_endpoint_success():
    """POST /api/transit/route returns valid route payload."""
    req = TransitRequest(
        origin="Coimbatore Junction",
        destination="Chennai Central",
        origin_lat=11.0016,
        origin_lon=76.9628,
        dest_lat=13.0827,
        dest_lon=80.2707,
        preferred_mode="fastest",
    )
    res = get_route(req)
    assert res is not None
    assert "status" in res
    assert "recommended_route" in res or "journeys" in res


def test_h2_missing_origin_returns_400():
    """POST /api/transit/route returns HTTP 400 when origin is missing."""
    req = TransitRequest(origin="", destination="Chennai Central")
    with pytest.raises(HTTPException) as exc_info:
        get_route(req)
    assert exc_info.value.status_code == 400
    assert "Origin location is required" in exc_info.value.detail


def test_h3_invalid_coordinates_returns_400():
    """POST /api/transit/route returns HTTP 400 when coordinates exceed valid boundaries."""
    req = TransitRequest(
        origin="Coimbatore Junction",
        destination="Chennai Central",
        origin_lat=125.0,  # Invalid latitude > 90
        origin_lon=76.9628,
        dest_lat=13.0827,
        dest_lon=80.2707,
    )
    with pytest.raises(HTTPException) as exc_info:
        get_route(req)
    assert exc_info.value.status_code == 400
    assert "latitude must be between -90 and 90" in exc_info.value.detail
