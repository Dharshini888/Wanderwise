import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.journey_stitcher import stitch_door_to_door_journey

class TestDepartureAwareDoorToDoor(unittest.TestCase):

    def test_custom_departure_time_orchestrator(self):
        """Verify that TransitOrchestrator respects explicit departure time and returns departure_plan."""
        plan = TransitOrchestrator.get_transit_plan(
            origin="Coimbatore",
            destination="Erode",
            origin_lat=11.0168,
            origin_lon=76.9558,
            dest_lat=11.3410,
            dest_lon=77.7172,
            date="Today",
            departure_type="custom",
            departure_time="15:00"
        )
        self.assertIn("departure_plan", plan)
        dep_plan = plan["departure_plan"]
        self.assertEqual(dep_plan["departure_type"], "custom")
        self.assertIn("3:00 PM", dep_plan["requested_departure_display"])

    def test_catchable_service_stitching(self):
        """Case 2: Service departs AFTER earliest station arrival + boarding buffer."""
        req_time = datetime(2026, 9, 27, 15, 0) # 3:00 PM
        train_dep = datetime(2026, 9, 27, 15, 30) # 3:30 PM (Station arrival ~3:15 PM + 5m buffer = 3:20 PM)
        train_arr = datetime(2026, 9, 27, 16, 45) # 4:45 PM

        candidate_route = {
            "provider": "RailRadar",
            "mode": "Rail",
            "departure_station": "Coimbatore Junction",
            "arrival_station": "Erode Junction",
            "departure_time": train_dep.isoformat(),
            "arrival_time": train_arr.isoformat(),
            "departure_time_display": "3:30 PM",
            "arrival_time_display": "4:45 PM",
            "duration_min": 75,
            "distance_km": 100.0,
            "verification_status": "Provider Verified",
            "legs": [{
                "boarding_stop": {"lat": 11.0010, "lon": 76.9664},
                "alighting_stop": {"lat": 11.3410, "lon": 77.7172}
            }]
        }

        journey = stitch_door_to_door_journey(
            route=candidate_route,
            origin_name="Gandhipuram",
            origin_lat=11.0183,
            origin_lon=76.9654,
            dest_name="Erode Collectorate",
            dest_lat=11.3410,
            dest_lon=77.7172,
            request_time=req_time,
            date_hint="Today"
        )

        self.assertIsNotNone(journey)
        self.assertTrue(journey["catchable"])
        self.assertIn("3:00 PM", journey["door_to_door_departure_display"])
        self.assertIn("duration_breakdown", journey)
        self.assertGreater(journey["duration_breakdown"]["waiting_min"], 0)

    def test_uncatchable_service_stitching(self):
        """Case 1: Service departs BEFORE earliest station arrival + boarding buffer."""
        req_time = datetime(2026, 9, 27, 15, 0) # 3:00 PM
        # Station arrival ~3:15 PM + 5m buffer = 3:20 PM. Train departs at 3:05 PM -> Cannot catch!
        train_dep = datetime(2026, 9, 27, 15, 5) 
        train_arr = datetime(2026, 9, 27, 16, 20)

        candidate_route = {
            "provider": "RailRadar",
            "mode": "Rail",
            "departure_station": "Coimbatore Junction",
            "arrival_station": "Erode Junction",
            "departure_time": train_dep.isoformat(),
            "arrival_time": train_arr.isoformat(),
            "departure_time_display": "3:05 PM",
            "arrival_time_display": "4:20 PM",
            "duration_min": 75,
            "distance_km": 100.0,
            "verification_status": "Provider Verified",
            "legs": [{
                "boarding_stop": {"lat": 11.0010, "lon": 76.9664},
                "alighting_stop": {"lat": 11.3410, "lon": 77.7172}
            }]
        }

        journey = stitch_door_to_door_journey(
            route=candidate_route,
            origin_name="Gandhipuram",
            origin_lat=11.0183,
            origin_lon=76.9654,
            dest_name="Erode Collectorate",
            dest_lat=11.3410,
            dest_lon=77.7172,
            request_time=req_time,
            date_hint="Today"
        )

        self.assertIsNotNone(journey)
        self.assertFalse(journey["catchable"])
        self.assertIn("Not catchable", journey["why_catchable"])

    def test_direct_road_departure_time(self):
        """Case 4: Direct road route departure & arrival time calculation."""
        req_time = datetime(2026, 9, 27, 15, 0) # 3:00 PM
        road_route = {
            "provider": "OSRM",
            "mode": "Driving",
            "duration_min": 75,
            "distance_km": 90.9,
            "verification_status": "Route Calculated"
        }

        journey = stitch_door_to_door_journey(
            route=road_route,
            origin_name="Gandhipuram",
            origin_lat=11.0183,
            origin_lon=76.9654,
            dest_name="Erode",
            dest_lat=11.3410,
            dest_lon=77.7172,
            request_time=req_time,
            date_hint="Today"
        )

        self.assertIsNotNone(journey)
        self.assertTrue(journey["catchable"])
        self.assertIn("3:00 PM", journey["door_to_door_departure_display"])
        self.assertIn("4:15 PM", journey["door_to_door_arrival_display"])
        self.assertEqual(journey["total_duration_min"], 75.0)

if __name__ == '__main__':
    unittest.main()
