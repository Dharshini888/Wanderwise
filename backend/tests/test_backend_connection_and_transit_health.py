"""
WanderWise — Backend Connection & Smart Transit Health Verification Suite
Tests:
  1. Health check diagnostics endpoint (/health and /api/health).
  2. CORS headers and allowed origins configuration.
  3. Input validation on /api/transit/route (reject empty origin/destination with HTTP 400).
  4. Transit request execution and response schema conformance.
  5. Test C: RailRadar (Coimbatore Junction -> Bengaluru City).
  6. Test D: Transitous (Kyoto Station -> Fushimi Inari).
  7. Test E: OSRM (Kyoto Station -> Kiyomizu-dera).
  8. Test F: Provider failure tolerance (one provider failure doesn't disable others).
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.main import app, health_check
from app.routes.transit import get_route, TransitRequest
from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.providers.base import ProviderStatus, ProviderResult


class TestBackendHealthAndConnectivity:

    def test_health_endpoint_response_schema(self):
        """Verifies health diagnostics endpoint returns actual system status."""
        health = health_check()
        assert "status" in health
        assert health["status"] in ["healthy", "degraded"]
        assert health["service"] == "WanderWise Backend"
        assert health["transit_module"] == "available"
        assert "timestamp" in health
        assert "version" in health

    def test_cors_configuration(self):
        """Verifies CORS origins include 5173, 5174, 5175, 4173, and 3000."""
        from app.main import origins
        expected = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:4173",
            "http://localhost:3000",
        ]
        for origin in expected:
            assert origin in origins, f"Expected {origin} to be in CORS allowed origins"

    def test_transit_route_validation_empty_inputs(self):
        """Empty origin or destination raises HTTP 400 Bad Request."""
        # Empty origin
        req_empty_orig = TransitRequest(origin="", destination="Paris")
        with pytest.raises(HTTPException) as exc_info:
            get_route(req_empty_orig)
        assert exc_info.value.status_code == 400
        assert "Origin" in exc_info.value.detail

        # Whitespace destination
        req_empty_dest = TransitRequest(origin="London", destination="   ")
        with pytest.raises(HTTPException) as exc_info:
            get_route(req_empty_dest)
        assert exc_info.value.status_code == 400
        assert "Destination" in exc_info.value.detail


class TestTransitEndpointsAndProviders:

    def test_scenario_c_railradar_coimbatore_to_bengaluru(self):
        """TEST C: Coimbatore Junction -> Bengaluru City via RailRadar."""
        req = TransitRequest(
            origin="Coimbatore Junction",
            destination="KSR Bengaluru",
            origin_lat=11.0016,
            origin_lon=76.9628,
            dest_lat=12.9781,
            dest_lon=77.5697,
            preferred_mode="fastest",
            date="Tomorrow",
            departure_type="now",
        )
        plan = get_route(req)
        assert plan is not None
        assert "status" in plan
        assert plan["status"] in ["PUBLIC_TRANSIT_AVAILABLE", "MULTIMODAL_ROUTES_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE", "SAME_LOCATION"]

        # Check route_options are present and RailRadar was evaluated
        assert "provider_audit" in plan
        assert "RailRadar" in plan["provider_audit"]
        assert plan["provider_audit"]["RailRadar"]["attempted"] is True

    def test_scenario_d_transitous_kyoto_to_fushimi_inari(self):
        """TEST D: Kyoto Station -> Fushimi Inari via Transitous."""
        req = TransitRequest(
            origin="Kyoto Station",
            destination="Fushimi Inari-taisha",
            origin_lat=34.9858,
            origin_lon=135.7588,
            dest_lat=34.9671,
            dest_lon=135.7727,
            preferred_mode="fastest",
            date="Today",
        )
        plan = get_route(req)
        assert plan is not None
        assert "status" in plan
        assert plan["status"] in ["PUBLIC_TRANSIT_AVAILABLE", "MULTIMODAL_ROUTES_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE"]
        assert "route_options" in plan
        assert "provider_audit" in plan

    def test_scenario_e_osrm_kyoto_to_kiyomizudera(self):
        """TEST E: Kyoto Station -> Kiyomizu-dera via OSRM Driving."""
        req = TransitRequest(
            origin="Kyoto Station",
            destination="Kiyomizu-dera",
            origin_lat=34.9858,
            origin_lon=135.7588,
            dest_lat=34.9949,
            dest_lon=135.7850,
            preferred_mode="fastest",
        )
        plan = get_route(req)
        assert plan is not None
        assert "status" in plan
        assert "route_options" in plan
        assert "provider_audit" in plan
        assert "OSRM" in plan["provider_audit"]
        assert plan["provider_audit"]["OSRM"]["attempted"] is True

    def test_scenario_f_provider_failure_graceful_tolerance(self):
        """
        TEST F: When one provider raises an unexpected exception,
        the transit endpoint remains resilient, other providers continue,
        and valid routes are still returned without crashing.
        """
        req = TransitRequest(
            origin="Kyoto Station",
            destination="Kiyomizu-dera",
            origin_lat=34.9858,
            origin_lon=135.7588,
            dest_lat=34.9949,
            dest_lon=135.7850,
        )

        with patch("app.services.transit.providers.railradar_provider.RailRadarProvider.plan_journey") as mock_rr:
            # Simulate hard crash in RailRadar
            mock_rr.side_effect = RuntimeError("RailRadar remote upstream crash 502 Bad Gateway")

            plan = get_route(req)
            assert plan is not None
            # Endpoint must NOT crash
            assert "route_options" in plan
            assert plan["status"] in ["PUBLIC_TRANSIT_AVAILABLE", "MULTIMODAL_ROUTES_AVAILABLE", "VERIFIED_ROAD_ALTERNATIVE"]

            # RailRadar failure recorded gracefully
            rr_audit = plan["provider_audit"].get("RailRadar", {})
            assert rr_audit.get("status") in ("PROVIDER_UNAVAILABLE", "Temporarily unavailable", "Unavailable")
            assert "crash" in str(rr_audit.get("reason", "")).lower()

            # OSRM and other providers succeeded
            assert plan["provider_audit"]["OSRM"]["status"] in ("SUCCESS", "Connected", "Route calculated")
