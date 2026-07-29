import sys
import os
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.services.trip_service import get_today_itinerary, toggle_activity_completion
from app.services.smart_replanner import SmartReplanner

def test_trip_today_suite():
    print("=== STARTING WANDERWISE v2.4 BACKEND SUITE (TEST_TRIP_TODAY.PY) ===")
    db = SessionLocal()
    try:
        # Create test users
        user1 = db.query(User).filter(User.email == "user1_today@wanderwise.com").first()
        if not user1:
            user1 = User(email="user1_today@wanderwise.com", name="User One", password="pw")
            db.add(user1)

        user2 = db.query(User).filter(User.email == "user2_today@wanderwise.com").first()
        if not user2:
            user2 = User(email="user2_today@wanderwise.com", name="User Two", password="pw")
            db.add(user2)

        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        today = date.today()
        start = today - timedelta(days=2)  # Started 2 days ago -> Today is Day 3
        end = today + timedelta(days=2)    # 5-day trip total

        # Create active trip for User 1
        trip1 = Trip(
            user_id=user1.id,
            destination="Bali",
            country="Indonesia",
            start_date=start,
            end_date=end,
            budget=1000.0,
            status="Active"
        )
        db.add(trip1)
        db.commit()
        db.refresh(trip1)

        # Create itinerary day 3
        day3 = ItineraryDay(trip_id=trip1.id, day_number=3, date=today, title="Ubud Waterfalls & Temple")
        db.add(day3)
        db.commit()
        db.refresh(day3)

        # Add activities for today
        now_h = datetime.now().hour
        s_past = f"{max(0, now_h-2):02d}:00"
        e_past = f"{max(1, now_h-1):02d}:00"

        act1 = ItineraryActivity(
            day_id=day3.id, title="Morning Yoga", start_time=s_past, end_time=e_past, order_index=1, weather_suitability="outdoor"
        )
        act2 = ItineraryActivity(
            day_id=day3.id, title="Ubud Palace & Museum", start_time="10:00", end_time="12:00", order_index=2, weather_suitability="indoor"
        )
        act3 = ItineraryActivity(
            day_id=day3.id, title="Tegallalang Rice Terrace", start_time="16:00", end_time="18:00", order_index=3, weather_suitability="outdoor"
        )
        db.add_all([act1, act2, act3])
        db.commit()
        db.refresh(act1)
        db.refresh(act2)
        db.refresh(act3)

        # --- 1. Test Day Calculation Logic ---
        print("\n--- 1. Testing Day Calculation Logic ---")
        res1 = get_today_itinerary(trip1.id, db, user_id=user1.id)
        print(f"Destination: {res1['destination']} | Calculated Day: {res1['current_day']} of {res1['total_days']}")
        assert res1["current_day"] == 3, f"Expected Day 3, got {res1['current_day']}"
        assert res1["total_days"] == 5, f"Expected 5 total days, got {res1['total_days']}"
        print("[SUCCESS] Day calculation verified!")

        # --- 2. Test Activity Completion Toggle & Timestamp ---
        print("\n--- 2. Testing Toggle Completion & Timestamping ---")
        toggle_res = toggle_activity_completion(trip_id=trip1.id, activity_id=act1.id, user_id=user1.id, db=db)
        assert toggle_res["is_completed"] == True
        assert toggle_res["completed_at"] is not None
        print(f"Activity #{act1.id} toggled completed: {toggle_res}")

        # Re-fetch today itinerary to verify status updated to 'completed'
        res_after = get_today_itinerary(trip1.id, db, user_id=user1.id)
        act1_processed = next(a for a in res_after["activities"] if a["id"] == act1.id)
        assert act1_processed["status"] == "completed"
        assert act1_processed["is_completed"] == True
        print("[SUCCESS] Activity completion toggle & status calculation verified!")

        # --- 3. Test Security User Isolation (User 2 accessing User 1's trip) ---
        print("\n--- 3. Testing User Isolation Security ---")
        try:
            get_today_itinerary(trip1.id, db, user_id=user2.id)
            assert False, "User 2 should NOT be allowed to access User 1's trip today endpoint"
        except ValueError:
            print("[SUCCESS] User isolation blocked unauthorized access correctly!")

        try:
            toggle_activity_completion(trip_id=trip1.id, activity_id=act1.id, user_id=user2.id, db=db)
            assert False, "User 2 should NOT be allowed to toggle User 1's activity completion"
        except ValueError:
            print("[SUCCESS] User isolation blocked unauthorized activity toggle correctly!")

        # --- 4. Test Smart Replanner Rule Engine ---
        print("\n--- 4. Testing Weather Smart Replanner Rule Engine ---")
        rain_rec = SmartReplanner.evaluate_weather_recommendation("Heavy Rain & Thunderstorms 24C", res_after["activities"])
        print(f"Smart Recommendation output for Rain: {rain_rec['title']} - {rain_rec['suggestions']}")
        assert rain_rec["has_recommendation"] == True
        assert rain_rec["type"] == "weather_rain"
        assert len(rain_rec["suggestions"]) > 0
        print("[SUCCESS] Smart Replanner rule engine verified!")

        # Cleanup test data
        db.delete(act1)
        db.delete(act2)
        db.delete(act3)
        db.delete(day3)
        db.delete(trip1)
        db.commit()

        print("\n=== ALL WANDERWISE v2.4 BACKEND TESTS PASSED CLEANLY (100%) ===")

    finally:
        db.close()

if __name__ == "__main__":
    test_trip_today_suite()
