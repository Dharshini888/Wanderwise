import os
import sys
from datetime import date, timedelta, datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.services.auth_service import hash_password, create_access_token
from app.services.trip_service import get_dashboard_widgets, generate_smart_rule_suggestions

client = TestClient(app)


def test_active_trip_dashboard():
    print("=== STARTING ACTIVE TRIP DASHBOARD & COMPLETION VERIFICATION ===")

    db = SessionLocal()
    try:
        # Setup test user
        existing_users = db.query(User).filter(User.email == "active_test_user@wanderwise.ai").all()
        if existing_users:
            u_ids = [u.id for u in existing_users]
            t_ids = [t.id for t in db.query(Trip.id).filter(Trip.user_id.in_(u_ids)).all()]
            if t_ids:
                d_ids = [d.id for d in db.query(ItineraryDay.id).filter(ItineraryDay.trip_id.in_(t_ids)).all()]
                if d_ids:
                    db.query(ItineraryActivity).filter(ItineraryActivity.day_id.in_(d_ids)).delete(synchronize_session=False)
                    db.query(ItineraryDay).filter(ItineraryDay.id.in_(d_ids)).delete(synchronize_session=False)
                db.query(Trip).filter(Trip.id.in_(t_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_(u_ids)).delete(synchronize_session=False)
            db.commit()

        user = User(name="Active User", email="active_test_user@wanderwise.ai", password=hash_password("password123"))
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "type": "access"})
        headers = {"Authorization": f"Bearer {token}"}

        today = date.today()
        start = today - timedelta(days=1)
        end = today + timedelta(days=3)

        # Create active trip
        active_trip = Trip(
            user_id=user.id,
            destination="Varkala",
            country="India",
            start_date=start,
            end_date=end,
            budget=1500.0,
            currency="USD"
        )
        db.add(active_trip)
        db.commit()
        db.refresh(active_trip)

        # Add Day 1 & Day 2
        day1 = ItineraryDay(trip_id=active_trip.id, day_number=1, date=start, title="Arrival in Varkala")
        day2 = ItineraryDay(trip_id=active_trip.id, day_number=2, date=today, title="Cliff & Beach Day")
        db.add(day1)
        db.add(day2)
        db.commit()
        db.refresh(day1)
        db.refresh(day2)

        # Add 3 activities for today (Day 2)
        act1 = ItineraryActivity(day_id=day2.id, title="Breakfast at Café Del Mar", start_time="08:30", end_time="09:30", order_index=1)
        act2 = ItineraryActivity(day_id=day2.id, title="Varkala Cliff Walk", start_time="10:00", end_time="11:30", transport_mode="walking", order_index=2)
        act3 = ItineraryActivity(day_id=day2.id, title="Janardhana Swamy Temple", start_time="12:00", end_time="13:30", order_index=3)
        db.add_all([act1, act2, act3])
        db.commit()
        db.refresh(act1)
        db.refresh(act2)
        db.refresh(act3)

        print("\n--- 1. Testing Active Trip Detection & Dashboard Widgets ---")
        widgets = get_dashboard_widgets(db, user.id)
        assert widgets["has_active_trip"] == True, "Active trip not detected"
        assert widgets["total_count"] == 3, f"Expected 3 activities today, got {widgets['total_count']}"
        assert widgets["completed_count"] == 0
        assert widgets["remaining_count"] == 3
        assert widgets["progress_percentage"] == 0.0
        assert widgets["current_activity"]["id"] == act1.id
        assert widgets["next_activity"]["id"] == act2.id
        print("[SUCCESS] Active trip & today's workspace detected cleanly!")

        print("\n--- 2. Testing Activity Completion Endpoint ---")
        resp_complete = client.patch(f"/api/activities/{act1.id}/complete", headers=headers)
        assert resp_complete.status_code == 200, f"Complete activity failed: {resp_complete.text}"
        comp_data = resp_complete.json()
        assert comp_data["completed"] == True
        assert comp_data["completed_at"] is not None

        # Re-query dashboard widgets
        widgets_after = get_dashboard_widgets(db, user.id)
        assert widgets_after["completed_count"] == 1
        assert widgets_after["remaining_count"] == 2
        assert widgets_after["progress_percentage"] == 33.3
        assert widgets_after["current_activity"]["id"] == act2.id
        assert widgets_after["next_activity"]["id"] == act3.id
        print("[SUCCESS] Activity completion persisted and auto-advanced next activity!")

        print("\n--- 3. Testing Activity Undo Completion Endpoint ---")
        resp_undo = client.patch(f"/api/activities/{act1.id}/undo", headers=headers)
        assert resp_undo.status_code == 200, f"Undo activity failed: {resp_undo.text}"
        undo_data = resp_undo.json()
        assert undo_data["completed"] == False
        assert undo_data["completed_at"] is None

        widgets_undo = get_dashboard_widgets(db, user.id)
        assert widgets_undo["completed_count"] == 0
        assert widgets_undo["remaining_count"] == 3
        assert widgets_undo["progress_percentage"] == 0.0
        print("[SUCCESS] Activity undo completed cleanly!")

        print("\n--- 4. Testing Rule-Based Suggestion Engine ---")
        dummy_weather = {
            "current": {"temperature": 34.0, "uv_index": 7.5, "precipitation": 0.0},
            "forecast": [{"precipitation_probability_max": 40, "uv_index_max": 8.0}]
        }
        suggestions = generate_smart_rule_suggestions(dummy_weather, [
            {"title": "Cliff Walk", "transport_mode": "walking"},
            {"title": "Temple"},
            {"title": "Lunch"},
            {"title": "Beach"},
            {"title": "Sunset Point"}
        ], active_trip)
        
        rule_ids = {s["id"] for s in suggestions}
        assert "rule_uv" in rule_ids, "UV rule suggestion missing"
        assert "rule_rain" in rule_ids, "Rain rule suggestion missing"
        assert "rule_heat" in rule_ids, "Heat rule suggestion missing"
        assert "rule_pace" in rule_ids, "Pace rule suggestion missing"
        print("[SUCCESS] Rule-based recommendation engine generated correct suggestions!")

        # Cleanup
        db.query(ItineraryActivity).filter(ItineraryActivity.day_id.in_([day1.id, day2.id])).delete(synchronize_session=False)
        db.query(ItineraryDay).filter(ItineraryDay.trip_id == active_trip.id).delete(synchronize_session=False)
        db.query(Trip).filter(Trip.id == active_trip.id).delete(synchronize_session=False)
        db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
        db.commit()

        print("\n=== ALL ACTIVE TRIP DASHBOARD TESTS PASSED (100%) ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_active_trip_dashboard()
