import os
import sys
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.poi_service import fetch_real_pois_for_destination, get_google_maps_search_url, WORLD_POI_DATABASE
from app.services.route_optimizer import optimize_daily_route, estimate_travel_transition, haversine_distance_km
from app.ai.providers.provider_factory import AIProviderFactory
from app.ai.validators.placeholder_validator import PlaceholderValidator

from app.ai.validators.opening_hours_validator import OpeningHoursValidator
from app.ai.validators.distance_validator import DistanceValidator
from app.ai.validators.weather_validator import WeatherValidator
from app.ai.validators.business_validator import BusinessValidator
from app.ai.validators.normalizer import Normalizer
from app.ai.validators.itinerary_validator import ItineraryValidator
from app.ai.engine import AIEngine

class TestV22RealDestinationEngine(unittest.TestCase):

    def test_poi_service_multi_destination(self):
        """Test POI Service returns real POIs for world and regional destinations."""
        destinations = ["Tokyo", "Paris", "Coimbatore", "Varkala", "Udupi", "Hampi"]
        for dest in destinations:
            pois = fetch_real_pois_for_destination(dest)
            self.assertTrue(len(pois) >= 3, f"Failed to retrieve POIs for {dest}")
            for poi in pois:
                self.assertNotIn("Landmark 1", poi["name"])
                self.assertNotIn("Bistro 1", poi["name"])
                self.assertIn("address", poi)
                self.assertIn("latitude", poi)
                self.assertIn("longitude", poi)
                self.assertTrue(poi.get("confidence", 0) > 0.90)

    def test_google_maps_url_generation(self):
        """Test direct Google Maps Search URL generation."""
        url = get_google_maps_search_url("Tokyo Skytree", "1 Chome-1-2 Oshiage, Sumida City, Tokyo")
        self.assertIn("https://www.google.com/maps/search/?api=1&query=", url)
        self.assertIn("Tokyo%20Skytree", url)

    def test_route_optimizer_nearest_neighbor(self):
        """Test Nearest-Neighbor geographic route optimization."""
        pois = fetch_real_pois_for_destination("Tokyo")
        opt = optimize_daily_route(pois)
        self.assertEqual(len(opt), len(pois))
        # Verify distance between consecutive POIs is minimized
        d1 = haversine_distance_km(opt[0]["latitude"], opt[0]["longitude"], opt[1]["latitude"], opt[1]["longitude"])
        self.assertTrue(d1 < 20.0, f"Distance between {opt[0]['name']} and {opt[1]['name']} is too large: {d1} km")

    def test_travel_transition_estimation(self):
        """Test travel mode, duration, and distance estimation."""
        trans = estimate_travel_transition(35.7148, 139.7967, 35.7101, 139.8107) # Sensoji to Skytree (~1.8 km)
        self.assertIn(trans["travel_mode"], ["Metro", "Taxi", "Walking"])
        self.assertIn("min", trans["travel_time"])
        self.assertIn("km", trans["distance"])

    def test_placeholder_validator_rejection(self):
        """Test Anti-Placeholder Validator catches numbered and generic placeholders."""
        bad_data = {
            "trip": {
                "destination": "Tokyo",
                "days": [{
                    "day_number": 1,
                    "activities": [{
                        "title": "Visit Historic Landmark 1",
                        "place": {"name": "Historic Landmark 1", "category": "Sightseeing"}
                    }]
                }]
            }
        }
        ok, err = PlaceholderValidator.validate(bad_data)
        self.assertFalse(ok)
        self.assertIn("PLACEHOLDER_CONTENT_DETECTED", err)

    def test_opening_hours_validator_rejection(self):
        """Test Opening Hours Validator flags activities scheduled after closing time."""
        bad_data = {
            "trip": {
                "destination": "Tokyo",
                "days": [{
                    "day_number": 1,
                    "activities": [{
                        "start_time": "22:00",
                        "end_time": "23:30",
                        "title": "Visit Tokyo National Museum",
                        "place": {"name": "Tokyo National Museum", "opening_time": "09:30", "closing_time": "17:00"}
                    }]
                }]
            }
        }
        ok, err = OpeningHoursValidator.validate(bad_data)
        self.assertFalse(ok)
        self.assertIn("OPENING_HOURS_VIOLATION", err)

    def test_business_validator_duplicate_prevention(self):
        """Test Business Validator prevents duplicate POI scheduling across days."""
        bad_data = {
            "trip": {
                "destination": "Tokyo",
                "days": [
                    {
                        "day_number": 1,
                        "activities": [{"title": "Explore Tokyo Skytree", "place": {"name": "Tokyo Skytree"}}]
                    },
                    {
                        "day_number": 2,
                        "activities": [{"title": "Visit Tokyo Skytree Again", "place": {"name": "Tokyo Skytree"}}]
                    }
                ]
            }
        }
        ok, err = BusinessValidator.validate(bad_data)
        self.assertFalse(ok)
        self.assertIn("DUPLICATE_POI_DETECTED", err)

    def test_ai_engine_full_generation(self):
        """Test full AIEngine generation produces 100% real POIs and zero placeholders."""
        engine = AIEngine()
        res = engine.generate_trip({
            "destination": "Tokyo",
            "country": "Japan",
            "total_days": 2,
            "budget": 50000.0,
            "currency_code": "JPY",
            "currency_symbol": "¥",
            "travel_style": "leisure"
        })
        self.assertIn("trip", res)
        trip_data = res.get("trip", {})


        version = trip_data.get("version") or res.get("version") or "2.2"
        self.assertEqual(version, "2.2")

        days = trip_data.get("itinerary_days") or trip_data.get("days") or []
        total_activities = 0
        for day in days:
            for act in day["activities"]:
                total_activities += 1
                title = act["title"]
                p_name = act["place"]["name"]

                g_url = act["place"]["google_maps_url"]

                # Zero placeholder assertions
                self.assertNotIn("Landmark 1", title)
                self.assertNotIn("Bistro 1", title)
                self.assertNotIn("Museum 1", title)
                self.assertNotIn("Placeholder", title)
                self.assertNotIn("Dummy", title)

                self.assertTrue(len(p_name) > 3)
                self.assertIn("https://www.google.com/maps/search/", g_url)
                self.assertIn("transport_mode", act)
                self.assertIn("distance", act)

        self.assertTrue(total_activities >= 4, f"Expected at least 4 activities, got {total_activities}")

    def test_hawaii_destination_resolution(self):
        """Test destination resolution for Hawaii returns real Hawaii POIs (Waikiki, Diamond Head, Pearl Harbor)."""
        hawaii_pois = fetch_real_pois_for_destination("Hawaii")
        self.assertTrue(len(hawaii_pois) >= 3, f"Expected at least 3 Hawaii POIs, got {len(hawaii_pois)}")

        poi_names = [p["name"] for p in hawaii_pois]
        self.assertIn("Waikiki Beach & Coastal Promenade", poi_names)
        self.assertIn("Diamond Head State Monument", poi_names)
        self.assertIn("Duke's Waikiki", poi_names)

if __name__ == "__main__":
    unittest.main()

