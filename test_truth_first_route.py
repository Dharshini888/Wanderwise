import sys
import os
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.route_optimizer import RouteOptimizer
from app.services.transit.live_transit_service import LiveTransitService

class TestTruthFirstRouteCalculation(unittest.TestCase):

    def test_osrm_departure_arrival_population(self):
        """
        Verify that OSRM routes return non-null departure_time and arrival_time
        when requested departure time is provided, along with Provider Calculated status.
        """
        result = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore",
            destination="Tiruchirappalli",
            origin_lat=11.0168,
            origin_lon=76.9558,
            dest_lat=10.7905,
            dest_lon=78.7047,
            departure_type="custom",
            departure_time="08:00",
            date="Today",
            preferred_mode="fastest"
        )
        
        self.assertIn("recommended_route", result)
        rec = result["recommended_route"]
        self.assertIsNotNone(rec, "Recommended route must not be None")
        
        # 1. Verification status must be Provider Calculated (or Route Calculated for leg)
        self.assertEqual(rec["provider"], "OSRM")
        self.assertEqual(rec["verification_status"], "Provider Calculated")
        
        # 2. Departure and arrival times must be populated (not Unavailable)
        self.assertIsNotNone(rec["departure_time"])
        self.assertIsNotNone(rec["arrival_time"])
        self.assertNotEqual(rec["departure_time_display"], "Unavailable")
        self.assertNotEqual(rec["arrival_time_display"], "Unavailable")
        self.assertIn("8:00 AM", rec["departure_time_display"])
        
        # 3. Fare must be None (Unavailable) for OSRM, transfers = 0
        self.assertIsNone(rec["fare"])
        self.assertEqual(rec["transfers"], 0)
        
        # 4. Provenance source dicts
        self.assertIn("verification", rec)
        self.assertIn("source", rec)
        self.assertEqual(rec["verification"]["level"], "provider_calculated")
        self.assertEqual(rec["source"]["duration"], "OSRM")

    def test_live_tracking_note_provider_aware(self):
        """
        Verify that live tracking response gives a provider/mode aware note
        for driving routes instead of a misleading bus-specific message.
        """
        driving_routes = [{
            "provider": "OSRM",
            "mode": "Driving",
            "duration_min": 120.0,
            "distance_km": 150.0
        }]
        res = LiveTransitService.get_live_tracking(
            origin_lat=11.0168,
            origin_lon=76.9558,
            dest_lat=10.7905,
            dest_lon=78.7047,
            routes=driving_routes
        )
        self.assertIn("road-network data", res["note"])

    def test_route_optimizer_custom_departure(self):
        """
        Verify RouteOptimizer.normalize_route handles custom departure_time parameter.
        """
        req_dep = datetime(2026, 9, 27, 8, 0)
        raw_itin = {
            "distance_km": 247.1,
            "duration_minutes": 216.6,
            "geometry": [[11.0, 76.9], [10.7, 78.7]]
        }
        norm = RouteOptimizer.normalize_route(
            provider="OSRM",
            mode="Road",
            raw_itinerary=raw_itin,
            origin_name="Coimbatore",
            dest_name="Tiruchirappalli",
            default_dist=247.1,
            departure_time=req_dep
        )
        
        self.assertIsNotNone(norm)
        self.assertEqual(norm["departure_time_display"], "8:00 AM")
        self.assertIn(norm["arrival_time_display"], ["11:36 AM", "11:37 AM"])
        self.assertEqual(norm["duration_min"], 216.6)
        self.assertEqual(norm["verification_status"], "Provider Calculated")

if __name__ == '__main__':
    unittest.main()
