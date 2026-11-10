import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.live_transit_service import LiveTransitService

class TestLiveTransitTracking(unittest.TestCase):

    def test_live_transit_orchestrator_integration(self):
        """Case A & B: Ensure live_tracking block is present in TransitOrchestrator response."""
        result = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore",
            destination="Tiruppur",
            origin_lat=11.0168,
            origin_lon=76.9558,
            dest_lat=11.1085,
            dest_lon=77.3411,
            preferred_mode="fastest",
            date="Tomorrow"
        )
        self.assertIn("live_tracking", result)
        live_info = result["live_tracking"]
        self.assertIn("status", live_info)
        self.assertIn("provider", live_info)
        self.assertIn("vehicle_positions", live_info)
        self.assertIn("last_updated", live_info)
        # Truth-First: when no key/feed exists, status should be unavailable, NOT fake live data
        self.assertIn(live_info["status"], ["live", "unavailable", "stale"])

    def test_no_fake_vehicles_when_unavailable(self):
        """Case B & C: Verify that unavailable response never fabricates vehicles or ETAs."""
        res = LiveTransitService.get_live_tracking(
            origin_lat=11.0168,
            origin_lon=76.9558,
            dest_lat=11.1085,
            dest_lon=77.3411,
        )
        if res["status"] == "unavailable":
            self.assertEqual(len(res["vehicle_positions"]), 0)
            self.assertEqual(res["provider"], "None")
            self.assertIsNone(res["last_updated"])

    def test_stale_feed_handling(self):
        """Case E: Test stale timestamp classification logic."""
        import time
        stale_time = time.time() - 600 # 10 minutes ago
        raw = [{
            "position": {"latitude": 11.0, "longitude": 76.9},
            "timestamp": stale_time,
            "vehicle": {"id": "BUS_STALE"},
            "route_name": "10A"
        }]
        res = LiveTransitService._normalize_live_response(raw, "TestProvider")
        self.assertEqual(res["status"], "stale")
        self.assertEqual(len(res["vehicle_positions"]), 1)
        self.assertEqual(res["vehicle_positions"][0]["vehicle_id"], "BUS_STALE")

    def test_live_feed_normalization(self):
        """Case A: Test valid fresh vehicle normalization."""
        import time
        fresh_time = time.time() - 30 # 30 seconds ago
        raw = [{
            "position": {"latitude": 11.0168, "longitude": 76.9558, "bearing": 180},
            "timestamp": fresh_time,
            "vehicle": {"id": "BUS_99"},
            "trip": {"route_id": "99", "trip_id": "TRIP_123"},
            "current_stop_name": "Central Bus Stand"
        }]
        res = LiveTransitService._normalize_live_response(raw, "TestProvider")
        self.assertEqual(res["status"], "live")
        self.assertEqual(res["provider"], "TestProvider")
        self.assertEqual(len(res["vehicle_positions"]), 1)
        veh = res["vehicle_positions"][0]
        self.assertEqual(veh["vehicle_id"], "BUS_99")
        self.assertEqual(veh["latitude"], 11.0168)
        self.assertEqual(veh["longitude"], 76.9558)
        self.assertEqual(veh["bearing"], 180)

if __name__ == '__main__':
    unittest.main()
