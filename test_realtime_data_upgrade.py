import sys
import os
import time
import unittest
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.live_transit_service import LiveTransitService
from app.services.transit.provider_registry import PROVIDER_CAPABILITIES, FALLBACK_CHAIN, get_provider_capabilities
from app.services.transit.providers.railradar_provider import RailRadarProvider

class TestRealtimeDataUpgrade(unittest.TestCase):

    def test_provider_capability_registry(self):
        """Verify provider registry and capabilities."""
        self.assertIn("OSRM", PROVIDER_CAPABILITIES)
        self.assertIn("RailRadar", PROVIDER_CAPABILITIES)
        self.assertIn("Transitous", PROVIDER_CAPABILITIES)
        
        osrm_cap = get_provider_capabilities("OSRM")
        self.assertFalse(osrm_cap["realtime"])
        self.assertEqual(osrm_cap["default_verification"], "PROVIDER_CALCULATED")

        rr_cap = get_provider_capabilities("RailRadar")
        self.assertTrue(rr_cap["realtime"])
        self.assertEqual(rr_cap["default_verification"], "SCHEDULE_VERIFIED")

    def test_railradar_live_status_structure(self):
        """Verify RailRadar live train status returns clean structure adhering to Truth-First rule."""
        status = RailRadarProvider.get_live_train_status("12676")
        self.assertIn("status", status)
        self.assertIn("available", status)
        if status["available"]:
            self.assertEqual(status["train_number"], "12676")
            self.assertIn("delay_min", status)
            self.assertIn("last_updated", status)
            self.assertEqual(status["source"], "RailRadar Live API")
        else:
            self.assertEqual(status["status"], "unavailable")

    def test_realtime_freshness_classification(self):
        """Verify freshness classification: fresh (<=300s) -> REALTIME_VERIFIED, stale (>300s) -> STALE_REALTIME."""
        fresh_time = datetime.now(timezone.utc).isoformat()
        fresh_veh = [{
            "position": {"latitude": 11.0168, "longitude": 76.9558},
            "timestamp": time.time() - 30, # 30s ago
            "vehicle": {"id": "FRESH_BUS"},
            "trip": {"route_id": "100"}
        }]
        res_fresh = LiveTransitService._normalize_live_response(fresh_veh, "TestProvider")
        self.assertEqual(res_fresh["status"], "live")

        stale_time = time.time() - 600 # 10 minutes ago
        stale_veh = [{
            "position": {"latitude": 11.0168, "longitude": 76.9558},
            "timestamp": stale_time,
            "vehicle": {"id": "STALE_BUS"},
            "trip": {"route_id": "100"}
        }]
        res_stale = LiveTransitService._normalize_live_response(stale_veh, "TestProvider")
        self.assertEqual(res_stale["status"], "stale")

    def test_realtime_route_status_endpoint_service(self):
        """Verify LiveTransitService.get_realtime_route_status returns canonical structure."""
        res = LiveTransitService.get_realtime_route_status(
            route_id="test_route_123",
            provider="OSRM"
        )
        self.assertEqual(res["route_id"], "test_route_123")
        self.assertEqual(res["provider"], "OSRM")
        self.assertEqual(res["verification"], "PROVIDER_CALCULATED")
        self.assertIn("realtime", res)
        self.assertFalse(res["realtime"]["available"])
        self.assertIn("sources", res)

    def test_canonical_route_schema_extension(self):
        """Verify that normalize_route returns canonical realtime & sources blocks."""
        raw_itin = {
            "distance_km": 100.0,
            "duration_minutes": 90.0,
            "departure_time": "2026-09-27T15:00:00+05:30",
            "arrival_time": "2026-09-27T16:30:00+05:30",
            "train_number": "12676",
            "train_name": "Kovai Express"
        }
        norm = RouteOptimizer.normalize_route(
            provider="RailRadar",
            mode="Rail",
            raw_itinerary=raw_itin,
            origin_name="Coimbatore",
            dest_name="Erode",
            default_dist=100.0
        )
        self.assertIsNotNone(norm)
        self.assertIn("verification", norm)
        self.assertIn("source", norm)
        self.assertEqual(norm["verification"]["level"], "scheduled")
        self.assertEqual(norm["verification_status"], "Provider Verified")

if __name__ == '__main__':
    unittest.main()
