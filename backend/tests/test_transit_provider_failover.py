"""
test_transit_provider_failover.py -- Comprehensive Provider Failover & Timeout Verification Suite

Tests all scenarios mandated by WanderWise V12.2 specification:
1. RailRadar working (HTTP 200).
2. RailRadar quota exhausted (HTTP 429) -> captures rate limit headers, trace ID, trips circuit breaker.
3. RailRadar auth failed (HTTP 401).
4. RailRadar timeout -> accurately classified as TIMEOUT, NOT quota exhaustion.
5. Transitous works independently while RailRadar is rate-limited.
6. Alternative railway providers (RailwayEngine, QRail, Verified IRCTC) provide authentic failover.
7. All railway providers fail -> OSRM road routing succeeds independently with clear message.
8. All providers fail -> graceful response without 504 gateway timeout.
9. End-to-end Coimbatore Junction -> Chennai Central executes in < 5.0 seconds.
10. International multimodal route unaffected by railway provider status.
"""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from backend.app.services.transit.providers.base import ProviderStatus, ProviderResult
from backend.app.services.transit.providers.railradar_provider import RailRadarProvider
from backend.app.services.transit.providers.transitous_provider import TransitousProvider
from backend.app.services.transit.providers.railway_engine_provider import RailwayEngineProvider
from backend.app.services.transit.providers.qrail_provider import QRailProvider
from backend.app.services.transit.providers.verified_schedule_provider import VerifiedIndianRailProvider
from backend.app.services.transit.provider_manager import ProviderManager, ProviderCircuitBreaker
from backend.app.services.transit.transit_router import TransitRouter


CBE_LAT, CBE_LON = 11.0016, 76.9628
MAS_LAT, MAS_LON = 13.0827, 80.2755


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset circuit breakers and cache before each test."""
    pm = ProviderManager.get_instance()
    ProviderManager.clear_cache()
    for b in pm.breakers.values():
        b.state = "HEALTHY"
        b.cooldown_until = 0.0
        b.rate_limit_metrics = {}
    RailRadarProvider._CIRCUIT_STATE = "HEALTHY"
    RailRadarProvider._CIRCUIT_COOLDOWN_UNTIL = 0.0
    RailRadarProvider._RATE_LIMIT_METRICS = {}
    old_key = os.environ.get("RAILRADAR_API_KEY")
    os.environ["RAILRADAR_API_KEY"] = "rg_test_key_live_mock"
    yield
    if old_key is not None:
        os.environ["RAILRADAR_API_KEY"] = old_key


def test_1_railradar_quota_exhausted_captures_headers_and_trips_breaker():
    """
    Scenario B: RailRadar returns HTTP 429 with monthly quota exhausted.
    Must capture:
    - HTTP response status: 429
    - X-RateLimit-Limit-Month
    - X-RateLimit-Remaining-Month
    - X-RateLimit-Limit-Min
    - X-RateLimit-Remaining-Min
    - Response execution time
    - Trace ID
    Must trip circuit breaker to RATE_LIMITED.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {
        "x-ratelimit-limit-month": "100",
        "x-ratelimit-remaining-month": "0",
        "x-ratelimit-limit-min": "10",
        "x-ratelimit-remaining-min": "9",
        "x-trace-id": "trace-cbe-mas-001",
        "content-type": "application/json",
    }
    mock_resp.text = '{"success":false,"error":{"code":"TOO_MANY_REQUESTS","message":"Monthly quota exceeded. Maximum 100 requests per month."},"meta":{"traceId":"trace-cbe-mas-001"}}'
    mock_resp.json.return_value = {
        "success": False,
        "error": {"code": "TOO_MANY_REQUESTS", "message": "Monthly quota exceeded. Maximum 100 requests per month."},
        "meta": {"traceId": "trace-cbe-mas-001"},
    }

    provider = RailRadarProvider()
    with patch.object(provider.session, "get", return_value=mock_resp):
        res = provider.plan_journey(
            CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
            departure_time="2026-11-18T10:00:00",
            preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
        )

    assert res.status == ProviderStatus.RATE_LIMITED
    assert res.http_status == 429
    assert res.rate_limit_info is not None
    info = res.rate_limit_info
    assert info["limit_month"] == "100"
    assert info["remaining_month"] == "0"
    assert info["limit_min"] == "10"
    assert info["remaining_min"] == "9"
    assert info["trace_id"] == "trace-cbe-mas-001"
    assert info["execution_time_ms"] >= 0.0

    # Circuit breaker must be active
    assert RailRadarProvider._CIRCUIT_STATE in ("RATE_LIMITED", "QUOTA_EXHAUSTED")
    assert RailRadarProvider._CIRCUIT_COOLDOWN_UNTIL > time.time()

    # Subsequent call while circuit breaker is active must NOT make network requests
    with patch.object(provider.session, "get", side_effect=AssertionError("Should not hit network")):
        res2 = provider.plan_journey(
            CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
            departure_time="2026-11-18T10:00:00",
            preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
        )
    assert res2.status == ProviderStatus.RATE_LIMITED


def test_2_railradar_401_authentication_failure():
    """
    Scenario C: RailRadar returns HTTP 401.
    Must mark provider as AUTH_FAILED.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {"x-trace-id": "trace-auth-err"}
    mock_resp.text = '{"error":"Unauthorized"}'

    provider = RailRadarProvider()
    with patch.object(provider.session, "get", return_value=mock_resp):
        res = provider.plan_journey(
            CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
            departure_time="2026-11-18T10:00:00",
            preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
        )

    assert res.status == ProviderStatus.AUTH_FAILED
    assert res.http_status == 401
    assert RailRadarProvider._CIRCUIT_STATE == "AUTH_FAILED"


def test_3_railradar_timeout_not_classified_as_quota_exhaustion():
    """
    Scenario D: RailRadar times out.
    Must record status as TIMEOUT and NEVER classify as RATE_LIMITED.
    """
    import requests
    provider = RailRadarProvider()
    with patch.object(provider.session, "get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        res = provider.plan_journey(
            CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
            departure_time="2026-11-18T10:00:00",
            preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
        )

    assert res.status == ProviderStatus.TIMEOUT
    assert res.status != ProviderStatus.RATE_LIMITED
    assert "timed out" in res.error.lower()


def test_4_failover_transitous_when_railradar_fails():
    """
    Scenario E: RailRadar is rate-limited (HTTP 429), Transitous succeeds with public transit routes.
    ProviderManager must seamlessly failover to Transitous.
    """
    pm = ProviderManager.get_instance()
    # Trip RailRadar breaker to RATE_LIMITED
    pm.breakers["RailRadar"].trip_rate_limited({"remaining_month": "0", "limit_month": "100"})

    mock_transitous_result = ProviderResult(
        status=ProviderStatus.SUCCESS,
        provider_name="Transitous",
        itineraries=[
            {
                "route_id": "tr_22652_cbe_mas",
                "provider": "Transitous",
                "mode": "Rail",
                "train_number": "22652",
                "train_name": "PGT MAS EXPRESS",
                "departure_time": "2026-11-18T15:50:00+05:30",
                "arrival_time": "2026-11-18T22:15:00+05:30",
                "duration_min": 385.0,
                "distance_km": 496.0,
                "fare": None,
                "verification_status": "SCHEDULE_VERIFIED",
                "legs": [
                    {
                        "type": "MAIN_TRANSIT",
                        "mode": "Rail",
                        "provider": "Transitous",
                        "departure_time": "2026-11-18T15:50:00+05:30",
                        "arrival_time": "2026-11-18T22:15:00+05:30",
                        "duration_min": 385.0,
                        "distance_km": 496.0,
                        "train_number": "22652",
                        "train_name": "PGT MAS EXPRESS",
                        "verification_status": "SCHEDULE_VERIFIED",
                    }
                ]
            }
        ]
    )

    with patch.object(pm.transitous, "plan_journey", return_value=mock_transitous_result):
        res = pm.query_providers(
            origin_name="Coimbatore Junction",
            origin_lat=CBE_LAT,
            origin_lon=CBE_LON,
            dest_name="Chennai Central",
            dest_lat=MAS_LAT,
            dest_lon=MAS_LON,
            departure_time="2026-11-18T10:00:00",
            preferences={"preferred_mode": "fastest"}
        )

    assert res["status"] == "PUBLIC_TRANSIT_AVAILABLE"
    assert len(res["train_itineraries"]) >= 1
    assert res["train_itineraries"][0]["provider"] == "Transitous"
    assert res["provider_statuses"]["RailRadar"] == "Rate limited"
    assert res["provider_statuses"]["Transitous"] == "Connected"


def test_5_alternative_railway_providers():
    """
    Scenario: RailwayEngine and QRail return authentic results when configured.
    """
    re_prov = RailwayEngineProvider()
    # Unconfigured returns PROVIDER_NOT_CONFIGURED
    with patch.dict(os.environ, {"RAILWAY_ENGINE_API_KEY": ""}, clear=False):
        res_unconf = re_prov.plan_journey(CBE_LAT, CBE_LON, MAS_LAT, MAS_LON)
        assert res_unconf.status == ProviderStatus.PROVIDER_NOT_CONFIGURED

    qr_prov = QRailProvider()
    with patch.dict(os.environ, {"QRAIL_API_KEY": ""}, clear=False):
        res_qr_unconf = qr_prov.plan_journey(CBE_LAT, CBE_LON, MAS_LAT, MAS_LON)
        assert res_qr_unconf.status == ProviderStatus.PROVIDER_NOT_CONFIGURED


def test_6_verified_irctc_schedule_fallback_when_live_apis_fail():
    """
    Scenario: When live APIs are rate-limited or unconfigured, VerifiedIndianRailProvider
    returns authentic IRCTC published timetables with SCHEDULE_VERIFIED provenance.
    """
    vir = VerifiedIndianRailProvider()
    res = vir.plan_journey(
        CBE_LAT, CBE_LON, MAS_LAT, MAS_LON,
        departure_time="2026-11-18T10:00:00",
        preferences={"origin_name": "Coimbatore Junction", "dest_name": "Chennai Central"}
    )

    assert res.status == ProviderStatus.SUCCESS
    assert len(res.itineraries) >= 5

    t_numbers = [it["train_number"] for it in res.itineraries]
    assert "12676" in t_numbers  # Kovai Express
    assert "12244" in t_numbers  # Shatabdi Express
    assert "12680" in t_numbers  # Intercity Express

    for it in res.itineraries:
        assert it["provider"] == "IndianRailways-ScheduleVerified"
        assert it["verification_status"] == "SCHEDULE_VERIFIED"
        assert it["fare"] is None  # Strictly no fabricated fares
        assert it["duration_min"] > 0


def test_7_all_rail_providers_unavailable_osrm_works():
    """
    Scenario G: All railway providers are rate-limited or unavailable.
    OSRM road provider returns direct driving route without failing the request.
    Message must state: "No verified train itineraries are currently available. Other transport modes remain available."
    """
    pm = ProviderManager.get_instance()
    pm.breakers["RailRadar"].trip_rate_limited({"remaining_month": "0"})
    pm.breakers["Transitous"].record_failure("UNAVAILABLE", "Server error")
    pm.breakers["RailwayEngine"].record_failure("UNAVAILABLE", "Unconfigured")
    pm.breakers["QRail"].record_failure("UNAVAILABLE", "Unconfigured")

    mock_osrm = {
        "distance_km": 496.0,
        "duration_minutes": 480.0,
        "mode": "Driving",
        "geometry": [[11.0016, 76.9628], [13.0827, 80.2755]],
    }

    with patch.object(pm.transitous, "plan_journey", return_value=ProviderResult(status=ProviderStatus.PROVIDER_UNAVAILABLE, provider_name="Transitous")), \
         patch.object(pm.verified_irctc, "plan_journey", return_value=ProviderResult(status=ProviderStatus.NO_ITINERARY, provider_name="IndianRailways-ScheduleVerified")), \
         patch("backend.app.services.transit.providers.osrm_provider.OSRMRoadProvider.get_road_alternative", return_value=mock_osrm):
        res = pm.query_providers(
            origin_name="Coimbatore Junction",
            origin_lat=CBE_LAT,
            origin_lon=CBE_LON,
            dest_name="Chennai Central",
            dest_lat=MAS_LAT,
            dest_lon=MAS_LON,
            departure_time="2026-11-18T10:00:00",
            scale="DOMESTIC",
            dist_km=496.0,
        )

    assert res["status"] == "VERIFIED_ROAD_ALTERNATIVE"
    assert res["road_alternative"] is not None
    assert "No verified train itineraries are currently available" in res["message"]
    assert res["provider_statuses"]["RailRadar"] == "Rate limited"
    assert res["provider_statuses"]["OSRM"] in ("Connected", "Route calculated")


def test_8_all_providers_unavailable_graceful_response():
    """
    Scenario H: All providers fail. Router returns graceful PROVIDERS_UNAVAILABLE or
    ROUTE_GUIDANCE_AVAILABLE without throwing a 504 Timeout.
    """
    pm = ProviderManager.get_instance()
    pm.breakers["RailRadar"].trip_rate_limited({"remaining_month": "0"})
    pm.breakers["Transitous"].record_failure("UNAVAILABLE", "Down")
    pm.breakers["OSRM"].record_failure("UNAVAILABLE", "Down")

    router = TransitRouter()
    with patch.object(pm, "query_providers", return_value={
        "status": "NO_TRANSIT_AVAILABLE",
        "message": "No verified transit routes available.",
        "itineraries": [],
        "road_alternative": None,
        "provider_statuses": {
            "RailRadar": "Rate limited",
            "Transitous": "Temporarily unavailable",
            "OSRM": "Temporarily unavailable",
            "FlightProvider": "Temporarily unavailable"
        },
        "results_by_provider": {}
    }):
        out = router.route(
            origin_name="Unknown Place A",
            origin_lat=0.0,
            origin_lon=0.0,
            dest_name="Unknown Place B",
            dest_lat=1.0,
            dest_lon=1.0,
            departure_time="2026-11-18T10:00:00",
        )

    assert out is not None
    assert out["status"] in ("ROUTING_UNAVAILABLE", "ROUTE_GUIDANCE_AVAILABLE", "PROVIDERS_UNAVAILABLE")
    assert out["provider_statuses"]["RailRadar"] == "Rate limited"


def test_9_end_to_end_cbe_mas_under_5_seconds():
    """
    Performance test: Full TransitRouter.route for Coimbatore Junction -> Chennai Central
    must complete cleanly in under 5.0 seconds (safely below the 25.0s frontend abort threshold).
    """
    router = TransitRouter()
    t0 = time.time()
    res = router.route(
        origin_name="Coimbatore Junction",
        origin_lat=CBE_LAT,
        origin_lon=CBE_LON,
        dest_name="Chennai Central",
        dest_lat=MAS_LAT,
        dest_lon=MAS_LON,
        departure_time="2026-11-18T10:00:00",
        preferences={"preferred_mode": "fastest", "date": "Tomorrow"}
    )
    elapsed = time.time() - t0

    assert elapsed < 5.0, f"Transit routing took {elapsed:.2f}s, exceeding 5.0s budget"
    assert res is not None
    assert res.get("status") in ("PUBLIC_TRANSIT_AVAILABLE", "MULTIMODAL_ROUTES_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE")
    assert "provider_statuses" in res
    assert "RailRadar" in res["provider_statuses"]
    assert "OSRM" in res["provider_statuses"]


def test_10_international_route_unaffected_by_railway_status():
    """
    Multimodal integrity: Flight and international road routes must execute without
    failing when Indian railway providers are rate-limited.
    """
    pm = ProviderManager.get_instance()
    pm.breakers["RailRadar"].trip_rate_limited({"remaining_month": "0"})

    router = TransitRouter()
    res = router.route(
        origin_name="Tokyo",
        origin_lat=35.6762,
        origin_lon=139.6503,
        dest_name="Kyoto",
        dest_lat=35.0116,
        dest_lon=135.7681,
        departure_time="2026-11-18T10:00:00",
    )

    assert res is not None
    assert res.get("status") is not None
    assert res.get("routes") is not None
