"""
Unit and Integration Tests for WanderWise Flight API Integration (AviationStack)
Validates HTTPS endpoint, strict key sanitization, error categorization, health check probes,
independent airport code testing (CJB, KIX), and truth-first fallback contract.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
import requests

from app.services.transit.providers.flight_provider import (
    FlightProvider,
    FLIGHTS_ENDPOINT,
    _mask_key,
    _sanitize_message,
    classify_provider_error,
    find_nearest_airport,
)
from app.services.transit.providers.base import ProviderStatus, ProviderResult


MOCK_SECRET_KEY = "test_secret_aviation_key_12345678"


class TestFlightProviderAviationStack:

    def test_https_endpoint_enforcement(self):
        """Verify the official AviationStack HTTPS endpoint is strictly used."""
        assert FLIGHTS_ENDPOINT.startswith("https://")
        assert "api.aviationstack.com/v1/flights" in FLIGHTS_ENDPOINT

    def test_api_key_loading(self, monkeypatch):
        """Verify API key is loaded from FLIGHT_API_KEY with AVIATIONSTACK_API_KEY fallback."""
        monkeypatch.setenv("FLIGHT_API_KEY", "primary_key_val")
        monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
        assert FlightProvider.get_api_key() == "primary_key_val"

        monkeypatch.delenv("FLIGHT_API_KEY", raising=False)
        monkeypatch.setenv("AVIATIONSTACK_API_KEY", "fallback_key_val")
        assert FlightProvider.get_api_key() == "fallback_key_val"

        monkeypatch.delenv("FLIGHT_API_KEY", raising=False)
        monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
        assert FlightProvider.get_api_key() is None

    def test_key_sanitization_and_masking(self):
        """Verify that API key is properly masked and never leaks into error messages or payloads."""
        key = "abcdef1234567890abcdef1234567890"
        masked = _mask_key(key)
        assert "abcd" in masked
        assert "7890" in masked
        assert "..." in masked
        assert key not in masked

        # Message sanitization
        leak_msg = f"Failed to connect using access_key={key} to endpoint https://api.aviationstack.com/v1/flights"
        sanitized = _sanitize_message(leak_msg, key)
        assert key not in sanitized
        assert masked in sanitized

    def test_health_check_when_key_unconfigured(self, monkeypatch):
        """When FLIGHT_API_KEY is not configured, health check returns clear unconfigured state."""
        monkeypatch.delenv("FLIGHT_API_KEY", raising=False)
        monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)

        res = FlightProvider.health_check(probe_network=True)
        assert res["configured"] is False
        assert res["authenticated"] is False
        assert res["status"] == "PROVIDER_NOT_CONFIGURED"
        assert res["category"] == "KEY_MISSING"

    @patch("requests.get")
    def test_health_check_authenticated_success(self, mock_get, monkeypatch):
        """When AviationStack returns HTTP 200 with data list, provider is authenticated."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "pagination": {"limit": 1, "offset": 0, "count": 1, "total": 500},
            "data": [{"flight": {"iata": "AI101"}, "airline": {"name": "Air India"}}]
        }
        mock_get.return_value = mock_resp

        res = FlightProvider.health_check(probe_network=True)
        assert res["configured"] is True
        assert res["authenticated"] is True
        assert res["reachable"] is True
        assert res["http_status"] == 200
        assert res["status"] == "AUTHENTICATED"
        assert res["category"] == "SUCCESS_AUTHENTICATED"
        assert MOCK_SECRET_KEY not in str(res)

    @patch("requests.get")
    def test_classify_invalid_api_key(self, mock_get, monkeypatch):
        """Verify classification of INVALID_API_KEY on HTTP 401 or AviationStack error 101."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {
            "error": {
                "code": 101,
                "type": "invalid_access_key",
                "info": f"You have not supplied a valid API Access Key. [Specified key: {MOCK_SECRET_KEY}]"
            }
        }
        mock_get.return_value = mock_resp

        res = FlightProvider.health_check(probe_network=True)
        assert res["configured"] is True
        assert res["authenticated"] is False
        assert res["category"] == "INVALID_API_KEY"
        assert res["http_status"] == 401
        # Check no secret leakage in error note or message
        assert MOCK_SECRET_KEY not in res["message"]
        assert MOCK_SECRET_KEY not in res["note"]

    @patch("requests.get")
    def test_classify_subscription_restriction(self, mock_get, monkeypatch):
        """Verify classification of SUBSCRIPTION_RESTRICTION on HTTP 403 or code 103/function_access_restricted."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {
            "error": {
                "code": "function_access_restricted",
                "type": "function_access_restricted",
                "info": "Your current subscription plan does not support this API function."
            }
        }
        mock_get.return_value = mock_resp

        res = FlightProvider.health_check(probe_network=True)
        assert res["configured"] is True
        assert res["authenticated"] is False
        assert res["category"] == "SUBSCRIPTION_RESTRICTION"
        assert res["http_status"] == 403
        assert "subscription plan does not support" in res["message"].lower()

    @patch("requests.get")
    def test_classify_quota_exhausted(self, mock_get, monkeypatch):
        """Verify classification of QUOTA_EXHAUSTED on HTTP 429 or code 104/usage_limit_reached."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.json.return_value = {
            "error": {
                "code": 104,
                "type": "usage_limit_reached",
                "info": "Your monthly API request limit has been reached."
            }
        }
        mock_get.return_value = mock_resp

        res = FlightProvider.health_check(probe_network=True)
        assert res["configured"] is True
        assert res["authenticated"] is False
        assert res["category"] == "QUOTA_EXHAUSTED"
        assert res["http_status"] == 429

    @patch("requests.get")
    def test_classify_timeout_and_connection_error(self, mock_get, monkeypatch):
        """Verify classification of TIMEOUT and CONNECTION_ERROR."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        # Timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out after 6 seconds")
        res_to = FlightProvider.health_check(probe_network=True)
        assert res_to["reachable"] is False
        assert res_to["category"] == "TIMEOUT"

        # Connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to establish DNS connection")
        res_ce = FlightProvider.health_check(probe_network=True)
        assert res_ce["reachable"] is False
        assert res_ce["category"] == "CONNECTION_ERROR"

    @patch("requests.get")
    def test_independent_airport_lookup_cjb_and_kix(self, mock_get, monkeypatch):
        """Test airport code querying for CJB and KIX independently."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        # 1. Test CJB with flights
        mock_resp_cjb = MagicMock()
        mock_resp_cjb.status_code = 200
        mock_resp_cjb.json.return_value = {
            "data": [
                {
                    "flight": {"iata": "6E5355", "number": "5355"},
                    "arrival": {"iata": "BLR", "airport": "Kempegowda International"},
                    "flight_status": "scheduled"
                }
            ]
        }
        mock_get.return_value = mock_resp_cjb
        cjb_res = FlightProvider.test_airport_code("CJB")
        assert cjb_res["iata"] == "CJB"
        assert cjb_res["status"] == "SUCCESS"
        assert cjb_res["active_flights_count"] == 1
        assert cjb_res["sample_flights"][0]["flight_number"] == "6E5355"

        # 2. Test KIX with flights
        mock_resp_kix = MagicMock()
        mock_resp_kix.status_code = 200
        mock_resp_kix.json.return_value = {
            "data": [
                {
                    "flight": {"iata": "CX566", "number": "566"},
                    "arrival": {"iata": "KIX", "airport": "Kansai International Airport"},
                    "flight_status": "active"
                }
            ]
        }
        mock_get.return_value = mock_resp_kix
        kix_res = FlightProvider.test_airport_code("KIX")
        assert kix_res["iata"] == "KIX"
        assert kix_res["status"] == "SUCCESS"
        assert kix_res["active_flights_count"] == 1

    @patch("requests.Session.get")
    def test_plan_journey_empty_search_results_no_mock_flights(self, mock_session_get, monkeypatch):
        """
        Truth-First Rule: If the provider returns empty search results (e.g. CJB -> KIX direct flights),
        NO mock or fake flights must be returned! Status must be NO_ITINERARY and category EMPTY_SEARCH_RESULTS.
        """
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "pagination": {"limit": 10, "offset": 0, "count": 0, "total": 0},
            "data": []
        }
        mock_session_get.return_value = mock_resp

        provider = FlightProvider()
        # CJB (11.0297, 77.0434) to KIX (34.4347, 135.2443)
        result = provider.plan_journey(
            origin_lat=11.0297,
            origin_lon=77.0434,
            dest_lat=34.4347,
            dest_lon=135.2443,
            origin_name="Coimbatore",
            dest_name="Kansai",
        )

        assert isinstance(result, ProviderResult)
        assert result.status == ProviderStatus.NO_ITINERARY
        assert result.category == "EMPTY_SEARCH_RESULTS"
        assert len(result.itineraries) == 0
        assert "no direct verified flight options" in result.note.lower()
        assert "cjb -> kix" in result.note.lower()

    @patch("requests.Session.get")
    def test_plan_journey_success_parsing(self, mock_session_get, monkeypatch):
        """When AviationStack returns scheduled flights, parse into validated itineraries."""
        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "flight_date": "2026-11-20",
                    "flight_status": "scheduled",
                    "departure": {
                        "airport": "Changi International Airport",
                        "iata": "SIN",
                        "scheduled": "2026-11-20T10:00:00+00:00"
                    },
                    "arrival": {
                        "airport": "Kansai International Airport",
                        "iata": "KIX",
                        "scheduled": "2026-11-20T17:30:00+00:00"
                    },
                    "airline": {
                        "name": "Singapore Airlines",
                        "iata": "SQ"
                    },
                    "flight": {
                        "number": "618",
                        "iata": "SQ618"
                    }
                }
            ]
        }
        mock_session_get.return_value = mock_resp

        provider = FlightProvider()
        # Singapore (1.3521, 103.8198) to Osaka/Kansai (34.4347, 135.2443)
        result = provider.plan_journey(
            origin_lat=1.3521,
            origin_lon=103.8198,
            dest_lat=34.4347,
            dest_lon=135.2443,
            origin_name="Singapore",
            dest_name="Osaka"
        )

        assert result.status == ProviderStatus.SUCCESS
        assert len(result.itineraries) == 1
        itin = result.itineraries[0]
        assert itin["flight_number"] == "SQ618"
        assert itin["airline_name"] == "Singapore Airlines"
        assert "Changi" in itin["origin_airport"]
        assert "Kansai" in itin["destination_airport"]
        assert itin["origin_iata"] == "SIN"
        assert itin["destination_iata"] == "KIX"
        assert itin["verification_status"] == "Provider Verified"
        assert itin["flight_duration_minutes"] in (390.0, 450.0) or itin["duration_minutes"] == 450
        assert any(l["mode"] == "Flight" for l in itin["legs"])

    def test_nearest_airport_resolution(self):
        """Verify nearest commercial serving airport resolution."""
        # Coimbatore (CJB)
        ap_cjb = find_nearest_airport(11.0168, 76.9558, max_radius_km=100)
        assert ap_cjb is not None
        assert ap_cjb["iata"] == "CJB"

        # Kansai / Osaka (KIX)
        ap_kix = find_nearest_airport(34.6937, 135.5023, max_radius_km=100)
        assert ap_kix is not None
        assert ap_kix["iata"] in ["KIX", "ITM"]

        # Singapore (SIN)
        ap_sin = find_nearest_airport(1.3521, 103.8198, max_radius_km=100)
        assert ap_sin is not None
        assert ap_sin["iata"] == "SIN"


class TestFlightProviderRoutes:
    """Verifies FastAPI transit debug routes report truthful diagnostic status."""

    @patch("requests.get")
    def test_debug_providers_route_reports_flight_health(self, mock_get, monkeypatch):
        """GET /api/transit/debug/providers includes authentic flight_provider health check."""
        from app.routes.transit import get_debug_providers

        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "pagination": {"limit": 1, "offset": 0, "count": 1, "total": 10},
            "data": [{"flight": {"iata": "AI101"}}]
        }
        mock_get.return_value = mock_resp

        data = get_debug_providers(probe=True)
        assert "flight_provider" in data
        fp = data["flight_provider"]
        assert fp["configured"] is True
        assert fp["authenticated"] is True
        assert fp["reachable"] is True
        assert fp["status"] == "AUTHENTICATED"
        assert fp["category"] == "SUCCESS_AUTHENTICATED"
        assert MOCK_SECRET_KEY not in str(data)

    @patch("requests.get")
    def test_debug_flight_endpoint_with_airport_tests(self, mock_get, monkeypatch):
        """GET /api/transit/debug/flight returns health and independent airport queries."""
        from app.routes.transit import get_debug_flight

        monkeypatch.setenv("FLIGHT_API_KEY", MOCK_SECRET_KEY)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "flight": {"iata": "6E5355"},
                    "arrival": {"iata": "BLR", "airport": "Bangalore"}
                }
            ]
        }
        mock_get.return_value = mock_resp

        data = get_debug_flight(test_cjb=True, test_kix=True)
        assert "health" in data
        assert "cjb_test" in data
        assert "kix_test" in data
        assert data["cjb_test"]["iata"] == "CJB"
        assert data["kix_test"]["iata"] == "KIX"
        assert MOCK_SECRET_KEY not in str(data)

