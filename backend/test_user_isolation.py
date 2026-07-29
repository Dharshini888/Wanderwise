import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense
from app.models.budget import Budget
from app.services.auth_service import hash_password, create_access_token

client = TestClient(app)


def test_user_isolation():
    print("=== STARTING TRIP VISIBILITY & USER ISOLATION VERIFICATION ===")

    db = SessionLocal()
    try:
        # 1. Setup User A and User B cleanly
        existing_users = db.query(User).filter(User.email.in_(["user_a_test@wanderwise.ai", "user_b_test@wanderwise.ai"])).all()
        if existing_users:
            u_ids = [u.id for u in existing_users]
            existing_trip_ids = [t.id for t in db.query(Trip.id).filter(Trip.user_id.in_(u_ids)).all()]
            if existing_trip_ids:
                db.query(Expense).filter(Expense.trip_id.in_(existing_trip_ids)).delete(synchronize_session=False)
                db.query(Budget).filter(Budget.trip_id.in_(existing_trip_ids)).delete(synchronize_session=False)
                db.query(Trip).filter(Trip.id.in_(existing_trip_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_(u_ids)).delete(synchronize_session=False)
            db.commit()

        user_a = User(name="User A", email="user_a_test@wanderwise.ai", password=hash_password("password123"))
        user_b = User(name="User B", email="user_b_test@wanderwise.ai", password=hash_password("password123"))
        db.add(user_a)
        db.add(user_b)
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        token_a = create_access_token({"sub": str(user_a.id), "type": "access"})
        token_b = create_access_token({"sub": str(user_b.id), "type": "access"})

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 2. User A creates 3 trips
        print("\n--- 1. Creating 3 Trips for User A ---")
        trips_a = []
        for i, dest in enumerate(["Tokyo", "Kyoto", "Osaka"]):
            resp = client.post("/api/trips/create", json={
                "user_id": user_a.id,
                "destination": dest,
                "country": "Japan",
                "start_date": "2026-10-01",
                "end_date": "2026-10-05",
                "budget": 3000.0,
                "currency": "USD",
                "force_create": True
            }, headers=headers_a)
            assert resp.status_code == 201, f"User A trip creation failed: {resp.text}"
            t_data = resp.json()
            assert t_data["user_id"] == user_a.id
            trips_a.append(t_data)
        assert len(trips_a) == 3
        print("[SUCCESS] User A created 3 trips successfully!")

        # 3. User B creates 2 trips
        print("\n--- 2. Creating 2 Trips for User B ---")
        trips_b = []
        for i, dest in enumerate(["London", "Edinburgh"]):
            resp = client.post("/api/trips/create", json={
                "user_id": user_b.id,
                "destination": dest,
                "country": "UK",
                "start_date": "2026-11-01",
                "end_date": "2026-11-04",
                "budget": 2000.0,
                "currency": "GBP",
                "force_create": True
            }, headers=headers_b)
            assert resp.status_code == 201, f"User B trip creation failed: {resp.text}"
            t_data = resp.json()
            assert t_data["user_id"] == user_b.id
            trips_b.append(t_data)
        assert len(trips_b) == 2
        print("[SUCCESS] User B created 2 trips successfully!")

        # 4. User A retrieves trips -> must return EXACTLY 3 trips
        print("\n--- 3. Verifying User Isolation for Trip Queries ---")
        resp_get_a = client.get(f"/api/trips/user/{user_a.id}", headers=headers_a)
        assert resp_get_a.status_code == 200
        data_a = resp_get_a.json()
        assert len(data_a) == 3, f"Expected 3 trips for User A, got {len(data_a)}"
        a_destinations = {t["destination"] for t in data_a}
        assert a_destinations == {"Tokyo", "Kyoto", "Osaka"}

        # 5. User B retrieves trips -> must return EXACTLY 2 trips
        resp_get_b = client.get(f"/api/trips/user/{user_b.id}", headers=headers_b)
        assert resp_get_b.status_code == 200
        data_b = resp_get_b.json()
        assert len(data_b) == 2, f"Expected 2 trips for User B, got {len(data_b)}"
        b_destinations = {t["destination"] for t in data_b}
        assert b_destinations == {"London", "Edinburgh"}
        print("[SUCCESS] User A received 3 trips, User B received 2 trips!")

        # 6. Dashboard Widget Totals are User Specific
        print("\n--- 4. Verifying User-Specific Dashboard Totals ---")
        widget_a = client.get(f"/api/trips/dashboard-widgets/{user_a.id}", headers=headers_a).json()
        widget_b = client.get(f"/api/trips/dashboard-widgets/{user_b.id}", headers=headers_b).json()
        
        assert widget_a["total_budget"] == 9000.0, f"Expected 9000.0 for User A, got {widget_a['total_budget']}"
        assert widget_b["total_budget"] == 4000.0, f"Expected 4000.0 for User B, got {widget_b['total_budget']}"
        print("[SUCCESS] Dashboard widgets are strictly user-isolated!")

        # 7. Cross-Account Access Prevention
        print("\n--- 5. Verifying Cross-Account Access Prevention ---")
        user_a_trip_id = trips_a[0]["id"]

        # Add expense to User A's trip
        exp_resp = client.post("/api/expenses/add", json={
            "trip_id": user_a_trip_id,
            "title": "Tokyo Ramen",
            "amount": 1500.0,
            "category": "Food",
            "currency": "JPY",
            "expense_date": "2026-10-01"
        }, headers=headers_a)
        assert exp_resp.status_code == 201, f"Expense creation failed: {exp_resp.status_code} {exp_resp.text}"

        # User B attempts to access User A's trip details
        unauth_trip_resp = client.get(f"/api/trips/{user_a_trip_id}", headers=headers_b)
        assert unauth_trip_resp.status_code == 404, f"User B accessed User A's trip: {unauth_trip_resp.status_code}"

        # User B attempts to access User A's expenses
        unauth_exp_resp = client.get(f"/api/expenses/trip/{user_a_trip_id}", headers=headers_b)
        assert unauth_exp_resp.status_code == 404, f"User B accessed User A's expenses: {unauth_exp_resp.status_code}"

        # User B attempts to delete User A's trip
        unauth_delete_resp = client.delete(f"/api/trips/{user_a_trip_id}", headers=headers_b)
        assert unauth_delete_resp.status_code == 404, f"User B deleted User A's trip: {unauth_delete_resp.status_code}"

        print("[SUCCESS] Cross-account access to trips and expenses blocked with HTTP 404!")

        # Cleanup
        created_trip_ids = [t["id"] for t in trips_a + trips_b]
        db.query(Expense).filter(Expense.trip_id.in_(created_trip_ids)).delete(synchronize_session=False)
        db.query(Budget).filter(Budget.trip_id.in_(created_trip_ids)).delete(synchronize_session=False)
        db.query(Trip).filter(Trip.id.in_(created_trip_ids)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db.commit()

        print("\n=== ALL USER ISOLATION TESTS PASSED CLEANLY (100%) ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_user_isolation()
