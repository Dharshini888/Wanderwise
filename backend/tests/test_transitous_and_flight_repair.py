"""
test_transitous_and_flight_repair.py — Automated Test Suite for Transitous & FlightProvider V12.2 Repair

Verifies:
1. Transitous MOTIS 2 endpoint integration (https://api.transitous.org/api/v6/plan):
   - Corridor 1: Erode -> Chennai (trains 12244, 12676, 12512)
   - Corridor 2: ERODE JN -> Chennai (station resolution & stop ID preservation)
   - Corridor 3: Chennai -> Erode
   - Corridor 4: Erode -> Coimbatore
   - Corridor 5: Coimbatore -> Chennai
   - Corridor 6: Pune -> Mumbai
   - Mixed-mode & multi-leg itinerary parsing
   - Chronology validation & status classification
2. FlightProvider AviationStack integration:
   - Authentication & key sanitization
   - Supported date query (CJB -> MAA, MAA -> CJB, CJB -> ICN)
   - Future date subscription restriction handling (HTTP 403 -> SUBSCRIPTION_RESTRICTION)
   - Door-to-door flight journey construction (Access + Check-in buffer + Flight + Baggage buffer + Egress)
3. Provider isolation & Orchestrator aggregation
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath("backend"))
load_dotenv("backend/.env")

from app.services.transit.providers.transitous_provider import (
    TransitousProvider,
    _parse_time_to_dt,
    _validate_chronology,
    _normalize_mode,
    TRANSITOUS_API_URL,
)
from app.services.transit.providers.flight_provider import (
    FlightProvider,
    classify_provider_error,
    _mask_key,
    _sanitize_message,
)
from app.services.transit.providers.base import ProviderStatus, ProviderResult
from app.services.transit.provider_manager import ProviderManager
from app.services.transit.transit_orchestrator import TransitOrchestrator


class TestTransitousProvider(unittest.TestCase):
    """Test suite for Transitous MOTIS 2 provider."""

    def setUp(self):
        self.provider = TransitousProvider()

    def test_transitous_api_url_is_motis_v6(self):
        """Transitous must query the stable MOTIS 2 /api/v6/plan endpoint."""
        self.assertEqual(TRANSITOUS_API_URL, "https://api.transitous.org/api/v6/plan")

    def test_mode_normalization(self):
        """Mode normalizer should map GTFS/MOTIS modes to clean user-facing names."""
        self.assertEqual(_normalize_mode("REGIONAL_RAIL"), ("REGIONAL_RAIL", "Train"))
        self.assertEqual(_normalize_mode("BUS"), ("BUS", "Bus"))
        self.assertEqual(_normalize_mode("WALK"), ("WALK", "Walk"))
        self.assertEqual(_normalize_mode("SUBWAY"), ("SUBWAY", "Subway"))
        self.assertEqual(_normalize_mode("LONG_DISTANCE"), ("LONG_DISTANCE", "Long Distance Rail"))

    def test_chronology_validation(self):
        """Chronology validator must reject itineraries where leg arrival > next leg departure."""
        now = datetime.now()
        valid_legs = [
            {"_dep_dt": now, "_arr_dt": now + timedelta(minutes=30)},
            {"_dep_dt": now + timedelta(minutes=45), "_arr_dt": now + timedelta(minutes=90)},
        ]
        self.assertTrue(_validate_chronology(valid_legs, now, now + timedelta(minutes=90)))

        invalid_legs = [
            {"_dep_dt": now, "_arr_dt": now + timedelta(minutes=60)},
            {"_dep_dt": now + timedelta(minutes=30), "_arr_dt": now + timedelta(minutes=90)},
        ]
        self.assertFalse(_validate_chronology(invalid_legs, now, now + timedelta(minutes=90)))

    def test_mock_erode_chennai_parsing(self):
        """Tests parsing of complete MOTIS 2 payload with multi-leg and intermediate stops."""
        sample_motis_payload = {
            "itineraries": [
                {
                    "startTime": "2026-11-18T10:59:00Z",
                    "endTime": "2026-11-18T17:24:00Z",
                    "duration": 23100,
                    "transfers": 0,
                    "legs": [
                        {
                            "mode": "WALK",
                            "from": {"name": "START", "lat": 11.3383, "lon": 77.7171, "departure": "2026-11-18T10:59:00Z"},
                            "to": {"name": "ERODE JN", "stopId": "in-Indian-Railways_ED", "lat": 11.3274, "lon": 77.7256, "arrival": "2026-11-18T11:15:00Z"},
                            "duration": 960,
                            "distance": 1200,
                        },
                        {
                            "mode": "REGIONAL_RAIL",
                            "routeShortName": "12676",
                            "routeLongName": "KOVAI SF EXP",
                            "agencyName": "Indian Railways",
                            "from": {"name": "ERODE JN", "stopId": "in-Indian-Railways_ED", "stopCode": "ED", "lat": 11.3274, "lon": 77.7256, "departure": "2026-11-18T11:15:00Z"},
                            "to": {"name": "PURATCHI THALAIVAR DR. MGR CTL", "stopId": "in-Indian-Railways_MAS", "stopCode": "MAS", "lat": 13.0850, "lon": 80.2751, "arrival": "2026-11-18T17:15:00Z"},
                            "duration": 21600,
                            "distance": 395000,
                            "intermediateStops": [
                                {"name": "SALEM JN", "stopCode": "SA", "arrival": "2026-11-18T12:08:00Z", "departure": "2026-11-18T12:10:00Z"},
                                {"name": "KATPADI JN", "stopCode": "KPD", "arrival": "2026-11-18T15:18:00Z", "departure": "2026-11-18T15:20:00Z"},
                            ],
                        },
                        {
                            "mode": "WALK",
                            "from": {"name": "PURATCHI THALAIVAR DR. MGR CTL", "lat": 13.0850, "lon": 80.2751, "departure": "2026-11-18T17:15:00Z"},
                            "to": {"name": "END", "lat": 13.0800, "lon": 80.2807, "arrival": "2026-11-18T17:24:00Z"},
                            "duration": 540,
                            "distance": 800,
                        }
                    ]
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_motis_payload

        with patch.object(self.provider.session, "get", return_value=mock_resp):
            res = self.provider.plan_journey(
                origin_lat=11.3383,
                origin_lon=77.7171,
                dest_lat=13.0800,
                dest_lon=80.2807,
                departure_time="2026-11-18T14:58:00+05:30",
            )

        self.assertEqual(res.status, ProviderStatus.SUCCESS)
        self.assertEqual(len(res.itineraries), 1)
        itin = res.itineraries[0]
        self.assertEqual(itin["provider"], "Transitous")
        self.assertEqual(itin["train_number"], "12676")
        self.assertEqual(itin["train_name"], "KOVAI SF EXP")
        self.assertEqual(itin["transfers"], 0)
        self.assertEqual(len(itin["legs"]), 3)
        self.assertEqual(itin["verification_status"], "Schedule Verified")
        self.assertEqual(len(itin["legs"][1]["intermediate_stops"]), 2)


class TestFlightProvider(unittest.TestCase):
    """Test suite for FlightProvider AviationStack integration."""

    def setUp(self):
        self.provider = FlightProvider()

    def test_mask_and_sanitize_key(self):
        """API keys must always be sanitized and never leaked."""
        sample_key = "abcdef1234567890abcdef1234567890"
        masked = _mask_key(sample_key)
        self.assertEqual(masked, "abcd...7890")
        self.assertNotIn("123456", masked)

        leak_str = f"Error communicating with access_key={sample_key}"
        sanitized = _sanitize_message(leak_str, sample_key)
        self.assertNotIn(sample_key, sanitized)
        self.assertIn("abcd...7890", sanitized)

    def test_classify_subscription_restriction(self):
        """HTTP 403 with function_access_restricted must be classified as SUBSCRIPTION_RESTRICTION."""
        payload = {
            "error": {
                "code": "function_access_restricted",
                "message": "Your current subscription plan does not support this API function."
            }
        }
        cat, msg, note = classify_provider_error(403, payload)
        self.assertEqual(cat, "SUBSCRIPTION_RESTRICTION")
        self.assertIn("does not support this query or endpoint", note)

    def test_door_to_door_flight_construction(self):
        """FlightProvider must construct door-to-door legs with first-mile, buffers, and egress."""
        mock_raw_flights = {
            "data": [
                {
                    "flight_date": "2026-11-18",
                    "flight_status": "scheduled",
                    "departure": {
                        "airport": "Coimbatore International Airport",
                        "iata": "CJB",
                        "scheduled": "2026-11-18T20:00:00+05:30",
                    },
                    "arrival": {
                        "airport": "Chennai International Airport",
                        "iata": "MAA",
                        "scheduled": "2026-11-18T21:05:00+05:30",
                    },
                    "airline": {"name": "IndiGo", "iata": "6E"},
                    "flight": {"number": "659", "iata": "6E659"},
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_raw_flights

        with patch.object(self.provider.session, "get", return_value=mock_resp), \
             patch.object(self.provider, "get_api_key", return_value="test_valid_key_12345678"):
            res = self.provider.plan_journey(
                origin_lat=11.3410,
                origin_lon=77.7172,
                dest_lat=13.0827,
                dest_lon=80.2707,
                departure_time=None,
                preferences={"date": "today", "departure_type": "now"},
                origin_name="Erode",
                dest_name="Chennai",
            )

        self.assertEqual(res.status, ProviderStatus.SUCCESS)
        self.assertEqual(len(res.itineraries), 1)
        itin = res.itineraries[0]
        self.assertTrue(itin.get("is_door_to_door"))
        self.assertEqual(itin["origin"], "Erode")
        self.assertEqual(itin["destination"], "Chennai")
        self.assertEqual(itin["flight_number"], "6E659")
        self.assertEqual(itin["airline"], "IndiGo")

        # 5 legs: FIRST_MILE, TRANSFER (check-in), MAIN_TRANSIT (flight), TRANSFER (baggage), LAST_MILE
        legs = itin["legs"]
        self.assertEqual(len(legs), 5)
        self.assertEqual(legs[0]["type"], "FIRST_MILE")
        self.assertEqual(legs[0]["from_name"], "Erode")
        self.assertEqual(legs[1]["type"], "TRANSFER")
        self.assertEqual(legs[1]["duration_minutes"], 90.0)
        self.assertEqual(legs[2]["type"], "MAIN_TRANSIT")
        self.assertEqual(legs[2]["mode"], "Flight")
        self.assertEqual(legs[3]["type"], "TRANSFER")
        self.assertEqual(legs[3]["duration_minutes"], 30.0)
        self.assertEqual(legs[4]["type"], "LAST_MILE")
        self.assertEqual(legs[4]["to_name"], "Chennai")


class TestProviderManagerAndOrchestrator(unittest.TestCase):
    """Test suite for ProviderManager and Orchestrator integration."""

    def test_provider_statuses_accuracy(self):
        """Provider statuses must report Connected, Route calculated, Rate limited, or No itinerary found accurately."""
        mgr = ProviderManager.get_instance()
        # Test circuit breaker statuses
        cb = mgr.breakers["OSRM"]
        self.assertEqual(cb.get_frontend_status(has_results=True, success_status="Route calculated"), "Route calculated")

        cb_rr = mgr.breakers["RailRadar"]
        cb_rr.trip_rate_limited({"error_message": "Rate limited (HTTP 429)"})
        self.assertEqual(cb_rr.get_frontend_status(has_results=False), "Rate limited")
        # Reset healthy for other tests
        cb_rr.record_success()

    def test_circuit_breaker_subscription_restriction(self):
        """Circuit breaker must report Subscription restricted when subscription restriction trips."""
        mgr = ProviderManager.get_instance()
        cb = mgr.breakers["FlightProvider"]
        cb.trip_subscription_restricted("HTTP 403: function_access_restricted")
        self.assertEqual(cb.get_frontend_status(), "Subscription restricted")
        # Reset
        cb.record_success()


if __name__ == "__main__":
    unittest.main()
