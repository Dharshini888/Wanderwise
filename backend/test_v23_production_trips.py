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
from app.models.expense import Expense
from app.services.auth_service import hash_password, create_access_token
from app.services.trip_service import normalize_destination

client = TestClient(app)


def test_v23_production_trips():
    print("=== STARTING WANDERWISE v2.3 PRODUCTION 'MY TRIPS' VERIFICATION ===")

    db = SessionLocal()
    try:
        # Cleanup existing test users
        for email in ["v23_user_a@wanderwise.ai", "v23_user_b@wanderwise.ai"]:
            existing = db.query(User).filter(User.email == email).all()
            if existing:
                u_ids = [u.id for u in existing]
                t_ids = [t.id for t in db.query(Trip.id).filter(Trip.user_id.in_(u_ids)).all()]
                if t_ids:
                    db.query(Expense).filter(Expense.trip_id.in_(t_ids)).delete(synchronize_session=False)
                    d_ids = [d.id for d in db.query(ItineraryDay.id).filter(ItineraryDay.trip_id.in_(t_ids)).all()]
                    if d_ids:
                        db.query(ItineraryActivity).filter(ItineraryActivity.day_id.in_(d_ids)).delete(synchronize_session=False)
                        db.query(ItineraryDay).filter(ItineraryDay.id.in_(d_ids)).delete(synchronize_session=False)
                    db.query(Trip).filter(Trip.id.in_(t_ids)).delete(synchronize_session=False)
                db.query(User).filter(User.id.in_(u_ids)).delete(synchronize_session=False)
                db.commit()

        # Create User A & User B
        user_a = User(name="User A", email="v23_user_a@wanderwise.ai", password=hash_password("password123"))
        user_b = User(name="User B", email="v23_user_b@wanderwise.ai", password=hash_password("password123"))
        db.add(user_a)
        db.add(user_b)
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        token_a = create_access_token({"sub": str(user_a.id), "type": "access"})
        token_b = create_access_token({"sub": str(user_b.id), "type": "access"})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        today = date.today()

        # 1. Create Trips for User A (Active, Upcoming in 3 days, Upcoming in 20 days, Completed)
        trip_active = Trip(
            user_id=user_a.id,
            destination="Bali",
            country="Indonesia",
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=4),
            budget=200000.0,
            currency="INR",
            travel_style="solo",
            status="Active"
        )
        trip_upcoming_near = Trip(
            user_id=user_a.id,
            destination="Tokyo",
            country="Japan",
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=10),
            budget=150000.0,
            currency="INR",
            travel_style="friends",
            status="Upcoming"
        )
        trip_upcoming_far = Trip(
            user_id=user_a.id,
            destination="New York",
            country="USA",
            start_date=today + timedelta(days=25),
            end_date=today + timedelta(days=30),
            budget=300000.0,
            currency="INR",
            travel_style="family",
            status="Upcoming"
        )
        trip_completed = Trip(
            user_id=user_a.id,
            destination="Rome",
            country="Italy",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=25),
            budget=100000.0,
            currency="INR",
            travel_style="solo",
            status="Completed"
        )
        db.add_all([trip_active, trip_upcoming_near, trip_upcoming_far, trip_completed])
        db.commit()
        db.refresh(trip_active)
        db.refresh(trip_upcoming_near)

        # Create Trip for User B
        trip_user_b = Trip(
            user_id=user_b.id,
            destination="London",
            country="UK",
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=12),
            budget=500000.0,
            currency="INR",
            travel_style="business",
            status="Upcoming"
        )
        db.add(trip_user_b)
        db.commit()

        # Add itinerary & expenses to trip_active
        day1 = ItineraryDay(trip_id=trip_active.id, day_number=1, date=today-timedelta(days=2), title="Day 1")
        day2 = ItineraryDay(trip_id=trip_active.id, day_number=2, date=today-timedelta(days=1), title="Day 2")
        day3 = ItineraryDay(trip_id=trip_active.id, day_number=3, date=today, title="Day 3")
        db.add_all([day1, day2, day3])
        db.commit()

        act1 = ItineraryActivity(day_id=day1.id, order_index=0, title="Tanah Lot", is_completed=True, ticket_price=500.0)
        act2 = ItineraryActivity(day_id=day2.id, order_index=0, title="Ubud Monkey Forest", is_completed=True, ticket_price=1000.0)
        act3 = ItineraryActivity(day_id=day3.id, order_index=0, title="Uluwatu Temple", is_completed=False, ticket_price=800.0, start_time="10:00")
        db.add_all([act1, act2, act3])

        exp1 = Expense(trip_id=trip_active.id, paid_by_user_id=user_a.id, amount=1500.0, title="Ticket Fees", category="SIGHTSEEING", expense_date=today)
        db.add(exp1)
        db.commit()

        print("--- 1. Testing User Isolation on Stats & Trips ---")
        res_a_stats = client.get("/api/trips/stats", headers=headers_a)
        assert res_a_stats.status_code == 200
        stats_a = res_a_stats.json()
        assert stats_a["totalTrips"] == 4
        assert stats_a["active"] == 1
        assert stats_a["upcoming"] == 2
        assert stats_a["completed"] == 1
        print("[SUCCESS] User A Stats verified (4 total trips)!")

        res_b_stats = client.get("/api/trips/stats", headers=headers_b)
        assert res_b_stats.status_code == 200
        stats_b = res_b_stats.json()
        assert stats_b["totalTrips"] == 1
        print("[SUCCESS] User B Stats verified (1 total trip, isolated from User A)!")

        print("\n--- 2. Testing Pagination & Sorting ---")
        res_paginated = client.get("/api/trips?page=1&limit=2&paginated=true", headers=headers_a)
        assert res_paginated.status_code == 200
        pag_data = res_paginated.json()
        assert pag_data["total"] == 4
        assert pag_data["limit"] == 2
        assert len(pag_data["trips"]) == 2
        assert pag_data["total_pages"] == 2
        print("[SUCCESS] Server-side Pagination verified!")

        print("\n--- 3. Testing Rich Metrics & Weather Cutoff ---")
        res_active_single = client.get(f"/api/trips/{trip_active.id}", headers=headers_a)
        assert res_active_single.status_code == 200
        active_json = res_active_single.json()
        assert active_json["trip_status"] == "Active"
        assert active_json["activities_total"] == 3
        assert active_json["activities_completed"] == 2
        assert active_json["budget_spent"] == 1500.0
        assert active_json["budget_health"] == "Healthy"
        assert active_json["cover_image"] is not None
        assert active_json["weather_summary"] is not None  # Weather included for Active trip!
        print("[SUCCESS] Active Trip Rich Metrics & Weather Preview verified!")

        res_far_single = client.get(f"/api/trips/{trip_upcoming_far.id}", headers=headers_a)
        assert res_far_single.status_code == 200
        far_json = res_far_single.json()
        assert far_json["trip_status"] == "Upcoming"
        assert far_json["weather_summary"] is None  # Weather null for trip starting >7 days away!
        print("[SUCCESS] Weather Cutoff verified (null for trips > 7 days away)!")

        print("\n--- 4. Testing Single Active Trip Spotlight ---")
        res_spotlight = client.get("/api/trips/spotlight", headers=headers_a)
        assert res_spotlight.status_code == 200
        spot_json = res_spotlight.json()
        assert spot_json.get("id") == trip_active.id
        assert spot_json.get("destination") == "Bali"
        print("[SUCCESS] Active Trip Spotlight hero card verified!")

        print("\n--- 5. Testing Destination Alias Normalization & Duplicate Detection ---")
        assert normalize_destination("NYC") == "New York"
        assert normalize_destination("BLR") == "Bengaluru"

        dup_payload = {
            "destination": "NYC",
            "start_date": (today + timedelta(days=25)).isoformat()
        }
        res_dup = client.post("/api/trips/check-duplicate", json=dup_payload, headers=headers_a)
        assert res_dup.status_code == 200
        dup_json = res_dup.json()
        assert dup_json["has_duplicate"] is True
        assert "Paris" in dup_json["message"] or "New York" in dup_json["message"]
        print("[SUCCESS] Alias Destination Normalization & Duplicate Detection verified!")

        print("\n--- 6. Testing Touch & Recently Viewed Trip ---")
        client.post(f"/api/trips/{trip_upcoming_near.id}/touch", headers=headers_a)
        res_recent = client.get("/api/trips/recently-viewed", headers=headers_a)
        assert res_recent.status_code == 200
        rec_json = res_recent.json()
        assert rec_json.get("id") == trip_upcoming_near.id
        assert rec_json.get("destination") == "Tokyo"
        print("[SUCCESS] Touch Endpoint & Recently Viewed Trip verified!")

        print("\n=== ALL WANDERWISE v2.3 PRODUCTION 'MY TRIPS' TESTS PASSED CLEANLY (100%) ===")

    finally:
        db.close()


if __name__ == "__main__":
    test_v23_production_trips()
