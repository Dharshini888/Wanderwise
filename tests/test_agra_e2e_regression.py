"""
test_agra_e2e_regression.py — End-to-End Regression Test Suite for Agra Scenario & WanderWise Fixes
"""

import os
import sys
import io
import unittest
from datetime import date, datetime, timedelta

# Ensure utf-8 output encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Force SQLite test database and mock AI provider
os.environ["DATABASE_URL"] = "sqlite:///./test_agra_regression.db"
os.environ["AI_PROVIDER"] = "mock"
os.environ["AI_DEFAULT_PROVIDER"] = "mock"
os.environ["AI_FALLBACK_PROVIDER"] = "mock"
os.environ["SECRET_KEY"] = "regression-test-secret-key-12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token
)
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.poi_service import DESTINATION_ALIASES, fetch_real_pois_for_destination
from app.services.trip_service import enrich_trip_response, get_today_itinerary
from app.services.ai_service import generate_structured_itinerary
from app.routes.trips import resolve_trip_preferences, _populate_trip_itinerary_from_ai
from app.schemas.trip_schemas import TripCreate

# Setup in-memory SQLite
test_engine = create_engine("sqlite:///./test_agra_regression.db", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class TestAgraE2ERegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        cls.db = TestSession()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        if os.path.exists("./test_agra_regression.db"):
            try:
                os.remove("./test_agra_regression.db")
            except Exception:
                pass

    def test_01_authentication_logic(self):
        """Test password hashing, JWT creation, decoding, expiration and 401 handling."""
        raw_pw = "Password123!"
        hashed = hash_password(raw_pw)
        self.assertTrue(verify_password(raw_pw, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

        # Test JWT token creation and decoding
        token_payload = {"sub": "42", "email": "traveler@wanderwise.test", "role": "USER"}
        access_tok = create_access_token(token_payload)
        refresh_tok = create_refresh_token(token_payload)

        decoded_acc = decode_token(access_tok)
        self.assertEqual(decoded_acc.get("sub"), "42")
        self.assertEqual(decoded_acc.get("type"), "access")

        decoded_ref = decode_token(refresh_tok)
        self.assertEqual(decoded_ref.get("sub"), "42")
        self.assertEqual(decoded_ref.get("type"), "refresh")

        # Invalid token returns empty dict -> cleanly causes 401
        self.assertEqual(decode_token("invalid.token.here"), {})
        self.assertEqual(decode_token(""), {})

    def test_02_budget_allocation_contract(self):
        """Validate door-to-door budget contract across all 8 categories for Ultra Luxury tier."""
        plan = BudgetAllocationService.calculate_plan(
            total_budget=200000.0,
            currency="INR",
            tier="ultra_luxury",
            destination="Agra",
            origin_city="Coimbatore",
            days=8,
            adults=10,
            children=0,
            travel_style="group",
            transport_mode="Mixed Transport",
            accommodation_preference="hotel"
        )

        # 1. Tier resolution & currency
        self.assertEqual(plan["tier_key"], "ultra_luxury")
        self.assertEqual(plan["tier_name"], "Ultra Luxury")
        self.assertEqual(plan["currency"], "INR")
        self.assertEqual(plan["total_user_budget"], 200000.0)

        # 2. All 8 required categories
        cats = plan["categories"]
        self.assertEqual(len(cats), 8)
        expected_keys = [
            "outbound_transport", "return_transport", "accommodation", "food",
            "local_transport", "activities", "other_fees", "contingency"
        ]
        self.assertEqual([c["key"] for c in cats], expected_keys)

        # 3. Sum of percentages must equal 100%
        self.assertAlmostEqual(sum(c["percentage"] for c in cats), 100.0, places=1)

        # 4. Sum of amounts must equal total budget
        self.assertAlmostEqual(sum(c["amount"] for c in cats), 200000.0, places=1)

        # 5. Ultra luxury specific percentage breakdown:
        # Outbound: 16%, Return: 16%, Accommodation: 38%, Food: 16%, Local Transit: 5%, Activities: 6%, Fees: 1%, Contingency: 2%
        cat_map = {c["key"]: c for c in cats}
        self.assertEqual(cat_map["outbound_transport"]["percentage"], 16.0)
        self.assertEqual(cat_map["outbound_transport"]["amount"], 32000.0)
        self.assertEqual(cat_map["return_transport"]["percentage"], 16.0)
        self.assertEqual(cat_map["return_transport"]["amount"], 32000.0)
        self.assertEqual(cat_map["accommodation"]["percentage"], 38.0)
        self.assertEqual(cat_map["accommodation"]["amount"], 76000.0)
        self.assertEqual(cat_map["food"]["percentage"], 16.0)
        self.assertEqual(cat_map["food"]["amount"], 32000.0)
        self.assertEqual(cat_map["local_transport"]["percentage"], 5.0)
        self.assertEqual(cat_map["local_transport"]["amount"], 10000.0)
        self.assertEqual(cat_map["activities"]["percentage"], 6.0)
        self.assertEqual(cat_map["activities"]["amount"], 12000.0)
        self.assertEqual(cat_map["other_fees"]["percentage"], 1.0)
        self.assertEqual(cat_map["other_fees"]["amount"], 2000.0)
        self.assertEqual(cat_map["contingency"]["percentage"], 2.0)
        self.assertEqual(cat_map["contingency"]["amount"], 4000.0)

        # 6. Total allocated categories exact match & 100% contract
        self.assertEqual(plan["total_allocated_categories"], 200000.0)
        self.assertEqual(plan["formatted_total_allocated"], "₹200,000")

        # 7. Truthful feasibility badging for 10 adults across 8 days
        self.assertFalse(plan["is_feasible"])
        self.assertEqual(plan["feasibility_status"], "Over Budget")
        self.assertEqual(plan["feasibility_color"], "rose")
        self.assertAlmostEqual(plan["total_estimated_cost"], 753128.25, delta=1.0)
        self.assertIn("Over Budget", plan["feasibility_badge"])

        # 8. Keys compatibility for frontend rendering
        self.assertIn("remaining_surplus_buffer", plan)
        self.assertIn("formatted_remaining_surplus", plan)
        self.assertIn("uncertainty_range", plan)
        self.assertIn("min", plan["uncertainty_range"])
        self.assertIn("max", plan["uncertainty_range"])
        self.assertIn("min_cost", plan["uncertainty_range"])
        self.assertIn("max_cost", plan["uncertainty_range"])
        self.assertIn("formatted_range", plan["uncertainty_range"])
        self.assertIn("formatted_uncertainty_range", plan)

        # 7. Cost provenance dictionary
        prov = plan["cost_provenance"]
        self.assertIsInstance(prov, dict)
        self.assertIn("flights", prov)
        self.assertIn("accommodation", prov)
        self.assertIn("food", prov)
        self.assertIn("local_transit", prov)
        self.assertIn("activities", prov)
        self.assertIn("pricing_source", plan)

    def test_03_poi_service_agra(self):
        """Verify Agra destination alias and verified real POIs."""
        self.assertEqual(DESTINATION_ALIASES.get("agra"), "agra")
        pois = fetch_real_pois_for_destination("Agra")
        self.assertTrue(len(pois) >= 15)

        names = [p["name"] for p in pois]
        self.assertIn("Taj Mahal", names)
        self.assertIn("Agra Fort", names)
        self.assertIn("Mehtab Bagh", names)
        self.assertIn("Fatehpur Sikri Imperial Complex", names)
        self.assertIn("Tomb of I'timad-ud-Daulah (Baby Taj)", names)
        self.assertIn("Akbar's Tomb (Sikandra)", names)
        self.assertIn("Deviram Sweets & Confectioners", names)
        self.assertIn("Peshawri at ITC Mughal", names)
        self.assertIn("Dasaprakash Pure Vegetarian Restaurant", names)

    def test_04_agra_end_to_end_scenario(self):
        """
        Execute full end-to-end trip generation for Agra scenario:
        - Destination: Agra
        - Origin: Coimbatore
        - Dates: Nov 12 - Nov 19, 2026 (8 days)
        - Travelers: 10 adults
        - Total Budget: ₹200,000 INR
        - Comfort Tier: Ultra Luxury
        - Pace: Balanced
        - Accessibility: Wheelchair Accessible, Avoid Long Walking
        - Dining: Street Food and Local Delicacies
        - Transportation: Mixed Transport
        - Directives: Avoid Crowds, Prioritize Hidden Gems
        """
        db = self.db

        # 1. Create User
        user = User(
            name="Arjun Sharma",
            email="arjun.agra@wanderwise.test",
            password=hash_password("Password123!"),
            currency="INR",
            preferred_budget="ultra_luxury"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Prepare TripCreate DTO with wizard inputs
        wizard_trip_preferences = {
            "destination": "Agra",
            "country": "India",
            "origin_city": "Coimbatore",
            "origin_airport": "CJB",
            "destination_airport": "AGR",
            "start_date": "2026-11-12",
            "end_date": "2026-11-19",
            "travel_type": "leisure",
            "travel_style": "group",
            "budget": "200000",
            "currency": "INR",
            "budget_type": "Ultra Luxury",
            "interests": "History, Street Food, Photography, Local Culture, Cafes, Hidden Gems, Festivals & Markets",
            "accommodation_preference": "hotel",
            "transportation": "Mixed Transport",
            "activity_pace": "balanced",
            "accessibility": "Wheelchair Accessible, Avoid Long Walking",
            "ai": "avoid_crowds,hidden_gems",
            "food": {
                "preferences": "Street Food, Local Delicacies",
                "allergies": ""
            },
            "daily_routine": {
                "wake_up_time": "08:00",
                "sleep_time": "22:30",
                "lunch_time": "13:00",
                "dinner_time": "19:30",
                "preferred_viewpoint": "sunset"
            },
            "weather": "mix"
        }

        trip_dto = TripCreate(
            destination="Agra",
            country="India",
            origin_city="Coimbatore",
            origin_airport="CJB",
            destination_airport="AGR",
            start_date=date(2026, 11, 12),
            end_date=date(2026, 11, 19),
            budget=200000.0,
            currency="INR",
            travel_type="leisure",
            travel_style="group",
            group_size=10,
            transportation="Mixed Transport",
            accommodation_preference="hotel",
            interests="History, Street Food, Photography, Local Culture, Cafes, Hidden Gems, Festivals & Markets",
            trip_preferences=wizard_trip_preferences,
            user_id=user.id,
            force_create=True
        )

        import time
        stage_timings = {}
        t_pipeline_start = time.perf_counter()

        # 3. Resolve preferences (Stage 1)
        t0 = time.perf_counter()
        resolved = resolve_trip_preferences(trip_dto, user)
        stage_timings["1_preference_resolution"] = (time.perf_counter() - t0) * 1000.0
        self.assertEqual(resolved["currency"], "INR")
        self.assertEqual(resolved["transportation"], "Mixed Transport")
        self.assertEqual(resolved["origin_city"], "Coimbatore")

        # 4. Create Trip database record (Stage 2)
        t0 = time.perf_counter()
        trip = Trip(
            user_id=user.id,
            title="Trip to Agra",
            destination="Agra",
            country="India",
            origin_city=resolved["origin_city"],
            origin_airport="CJB",
            destination_airport="AGR",
            start_date=date(2026, 11, 12),
            end_date=date(2026, 11, 19),
            budget=200000.0,
            currency=resolved["currency"],
            travel_type="leisure",
            travel_style="group",
            transportation=resolved["transportation"],
            accommodation_preference=resolved["accommodation_preference"],
            interests=resolved["interests"],
            group_size=10,
            trip_preferences=resolved["trip_preferences"]
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        stage_timings["2_trip_db_persistence"] = (time.perf_counter() - t0) * 1000.0

        # 5. Generate structured AI itinerary (Stage 3)
        days_count = max(1, (trip.end_date - trip.start_date).days + 1)
        self.assertEqual(days_count, 8)

        t0 = time.perf_counter()
        ai_data = generate_structured_itinerary(
            destination=trip.destination,
            days=days_count,
            budget=trip.budget,
            interests=trip.interests,
            travel_style=trip.travel_style,
            group_size=trip.group_size,
            currency=trip.currency,
            country=trip.country,
            origin_city=trip.origin_city,
            origin_airport=trip.origin_airport,
            destination_airport=trip.destination_airport,
            accommodation_preference=trip.accommodation_preference,
            transportation=trip.transportation,
            travel_companion=trip.travel_style,
            start_date=str(trip.start_date),
            end_date=str(trip.end_date),
            trip_preferences=trip.trip_preferences,
            language="English"
        )
        stage_timings["3_ai_generation"] = (time.perf_counter() - t0) * 1000.0

        # 6. Populate database from AI output (Stage 4)
        t0 = time.perf_counter()
        _populate_trip_itinerary_from_ai(db, trip, ai_data)
        stage_timings["4_db_itinerary_population"] = (time.perf_counter() - t0) * 1000.0

        # 7. Enrich trip response (Stage 5)
        t0 = time.perf_counter()
        enriched = enrich_trip_response(trip, db)
        stage_timings["5_response_enrichment"] = (time.perf_counter() - t0) * 1000.0

        # ─── VERIFICATIONS ──────────────────────────────────────────

        # A. Core Trip Verification
        self.assertEqual(enriched["destination"], "Agra")
        self.assertEqual(enriched["duration_days"], 8)
        self.assertEqual(enriched["group_size"], 10)
        self.assertEqual(enriched["budget"], 200000.0)
        self.assertEqual(enriched["currency"], "INR")
        self.assertEqual(enriched["currency_symbol"], "₹")
        self.assertEqual(enriched["transportation"], "Mixed Transport")

        # B. Financial Plan & Categories
        budget_plan = enriched.get("budget_plan")
        self.assertIsNotNone(budget_plan)
        self.assertEqual(budget_plan["tier_key"], "ultra_luxury")
        self.assertEqual(len(budget_plan["categories"]), 8)
        self.assertEqual(budget_plan["total_user_budget"], 200000.0)
        self.assertIn("remaining_surplus_buffer", budget_plan)
        self.assertIn("formatted_remaining_surplus", budget_plan)

        # Ensure cost_provenance is a dict that frontend safely renders
        prov = budget_plan["cost_provenance"]
        self.assertIsInstance(prov, dict)
        self.assertEqual(set(prov.keys()), {"flights", "accommodation", "food", "local_transit", "activities"})

        # C. Itinerary Days & Activities Count
        itinerary_days = enriched.get("itinerary_days", [])
        self.assertEqual(len(itinerary_days), 8, f"Expected 8 days, got {len(itinerary_days)}")

        total_activities = sum(len(d.get("activities", [])) for d in itinerary_days)
        self.assertTrue(total_activities >= 32, f"Expected >= 32 activities, got {total_activities}")

        # D. Geographic Feasibility & Real Places
        for d in itinerary_days:
            day_num = d["day_number"]
            acts = d.get("activities", [])
            self.assertTrue(len(acts) >= 4, f"Day {day_num} has only {len(acts)} activities")

            # Overnight stay verification
            self.assertIn("ITC Mughal", d.get("overnight_stay", ""))

            for act in acts:
                # Real place name & coordinates
                self.assertIsNotNone(act.get("title"))
                place = act.get("place", {})
                self.assertIsNotNone(place.get("latitude"))
                self.assertIsNotNone(place.get("longitude"))

                # Meal / Restaurant distinction
                if act.get("is_dining") or act.get("activity_type") == "meal":
                    self.assertNotEqual(act.get("formatted_cost"), "Free Entry")
                    self.assertTrue(act.get("meal_cost", 0) > 0 or "Est. Meal" in act.get("formatted_cost", ""))

        # E. Sunset Activity at Mehtab Bagh (Day 4)
        day_4 = next(d for d in itinerary_days if d["day_number"] == 4)
        day_4_acts = day_4["activities"]
        sunset_act = next((a for a in day_4_acts if "Mehtab Bagh" in a["title"]), None)
        self.assertIsNotNone(sunset_act)
        self.assertEqual(sunset_act["time_slot"], "evening")
        self.assertTrue("16:30" <= sunset_act["start_time"] <= "18:00")

        # F. Sunrise & Crowd-Avoidance at Taj Mahal (Day 2)
        day_2 = next(d for d in itinerary_days if d["day_number"] == 2)
        taj_act = next((a for a in day_2["activities"] if "Taj Mahal" in a["title"]), None)
        self.assertIsNotNone(taj_act)
        self.assertEqual(taj_act["time_slot"], "morning")
        self.assertEqual(taj_act["start_time"], "06:00")
        self.assertIn("crowd", taj_act["ai_reason"].lower())

        # G. Excursion to Fatehpur Sikri (Day 5)
        day_5 = next(d for d in itinerary_days if d["day_number"] == 5)
        self.assertEqual(day_5.get("base_city"), "Fatehpur Sikri")
        day_5_titles = [a["title"] for a in day_5["activities"]]
        self.assertTrue(any("Fatehpur Sikri" in t for t in day_5_titles))
        self.assertTrue(any("Buland Darwaza" in t for t in day_5_titles))

        # H. Today Execution / Upcoming View Verification (Stage 6)
        t0 = time.perf_counter()
        today_data = get_today_itinerary(trip.id, db, user.id)
        stage_timings["6_today_itinerary_fetch"] = (time.perf_counter() - t0) * 1000.0

        total_pipeline_time = time.perf_counter() - t_pipeline_start
        self.assertLess(total_pipeline_time, 60.0, f"Expected pipeline duration < 60s, took {total_pipeline_time:.2f}s")

        self.assertIsNotNone(today_data)
        self.assertTrue(today_data.get("is_upcoming_trip"))
        self.assertEqual(today_data.get("trip_status"), "Upcoming")
        self.assertIn("12 Nov 2026", today_data.get("upcoming_notice", ""))

        # Verify route_summary stops and coordinates for TripItineraryMap
        route_summary = today_data.get("route_summary")
        self.assertIsNotNone(route_summary)
        stops = route_summary.get("stops", [])
        self.assertTrue(len(stops) >= 4, f"Expected >= 4 stops in route_summary, got {len(stops)}")
        for stop in stops:
            self.assertIsNotNone(stop.get("latitude"))
            self.assertIsNotNone(stop.get("longitude"))
            self.assertIsNotNone(stop.get("title"))

        # Verify today's processed activities have place details and coordinates
        today_acts = today_data.get("activities", [])
        self.assertTrue(len(today_acts) >= 4)
        for act in today_acts:
            self.assertIsNotNone(act.get("place"))
            self.assertIsNotNone(act["place"].get("latitude"))
            self.assertIsNotNone(act["place"].get("longitude"))

        print("\n" + "="*70)
        print("STAGE TIMINGS BREAKDOWN (Target: < 60,000 ms)")
        print("="*70)
        for stage, duration_ms in stage_timings.items():
            print(f"  • {stage:<30}: {duration_ms:>8.2f} ms")
        print(f"  Total Pipeline Time           : {total_pipeline_time * 1000.0:>8.2f} ms ({total_pipeline_time:.2f} s)")
        print("="*70)

        print(f"\n[PASS] 8-Day Agra Itinerary generated with {total_activities} activities across {len(itinerary_days)} days.")
        print(f"[PASS] Budget Plan: Tier={budget_plan['tier_name']}, Allocated={budget_plan['formatted_total_allocated']} (100% contract).")
        print(f"[PASS] Feasibility: status={budget_plan['feasibility_status']}, color={budget_plan['feasibility_color']}.")
        print(f"[PASS] All 8 budget categories verified and sum to ₹200,000 INR.")
        print(f"[PASS] Real places, geographic coordinates, and meal costs verified.")
        print(f"[PASS] Today's itinerary and map route summary verified with {len(stops)} stops.")


if __name__ == "__main__":
    unittest.main()
