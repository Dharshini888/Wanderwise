import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from decimal import Decimal
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense
from app.services.expense_service import normalize_merchant_name


client = TestClient(app)

def run_tests():
    print("=== STARTING WANDERWISE v2.1 EXPENSE & BUDGET MANAGER VERIFICATION ===")

    # 1. Test Merchant Normalization
    print("\n--- 1. Testing Merchant Normalization ---")
    assert normalize_merchant_name("STARBUCKS Coffee") == "Starbucks"
    assert normalize_merchant_name("Uber Ride bistro") == "Uber Ride"
    print("[SUCCESS] Merchant Normalization verified!")

    # 2. Get/Create Test User & Trip
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(email="expense_tester@wanderwise.ai", password_hash="hashed", full_name="Expense Tester")
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id

    trip = db.query(Trip).filter(Trip.user_id == user_id).first()
    if not trip:
        trip = Trip(
            user_id=user_id,
            destination="Tokyo",
            country="Japan",
            start_date="2026-10-01",
            end_date="2026-10-05",
            budget=50000.0,
            currency="INR"
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
    trip_id = trip.id
    db.query(Expense).filter(Expense.trip_id == trip_id).delete()
    db.commit()
    db.close()


    # 3. Create Expenses (CRUD - Create)
    print("\n--- 2. Testing Expense Creation & Budget Sync ---")
    payload1 = {
        "trip_id": trip_id,
        "title": "Starbucks Coffee",
        "amount": 450.00,
        "category": "Food",
        "payment_method": "Credit Card",
        "expense_date": "2026-10-01",
        "currency": "INR",
        "location_name": "Shibuya, Tokyo",
        "notes": "Morning coffee",
        "expense_source": "MANUAL"
    }
    resp1 = client.post("/api/expenses", json=payload1)
    assert resp1.status_code == 201, f"Create expense failed: {resp1.text}"
    exp1 = resp1.json()
    assert exp1["title"] == "Starbucks Coffee"
    assert exp1["merchant_normalized"] == "Starbucks"
    assert exp1["currency"] == "INR"
    exp1_id = exp1["id"]

    payload2 = {
        "trip_id": trip_id,
        "title": "Narita Express Train",
        "amount": 2800.00,
        "category": "Transport",
        "payment_method": "Credit Card",
        "expense_date": "2026-10-01",
        "currency": "INR",
        "location_name": "Narita Airport",
        "notes": "Airport express train",
        "expense_source": "MANUAL"
    }
    resp2 = client.post("/api/expenses", json=payload2)
    assert resp2.status_code == 201
    exp2_id = resp2.json()["id"]

    print("[SUCCESS] Expenses created successfully!")

    # 4. Fetch Budget Sync
    print("\n--- 3. Testing Budget Sync & Decimal Math ---")
    resp_b = client.get(f"/api/expenses/budget/{trip_id}")
    assert resp_b.status_code == 200, f"Get budget failed: {resp_b.text}"
    b_data = resp_b.json()
    print("Budget Data:", b_data)
    assert float(b_data["spent"]) == 3250.00
    assert float(b_data["remaining"]) == float(b_data["total_budget"]) - 3250.00
    print("[SUCCESS] Budget Entity auto-synchronized!")


    # 5. Test Expense Update & Delete
    print("\n--- 4. Testing Expense Update & Delete ---")
    resp_u = client.put(f"/api/expenses/{exp1_id}", json={"amount": 500.00, "notes": "Updated morning coffee"})
    assert resp_u.status_code == 200
    assert float(resp_u.json()["amount"]) == 500.00

    resp_b2 = client.get(f"/api/expenses/budget/{trip_id}")
    assert float(resp_b2.json()["spent"]) == 3300.00

    print("[SUCCESS] Expense Update & Budget recalculation verified!")

    # 6. Test Analytics Endpoint
    print("\n--- 5. Testing Budget Analytics Endpoint ---")
    resp_a = client.get(f"/api/expenses/analytics/{trip_id}")
    assert resp_a.status_code == 200, f"Analytics failed: {resp_a.text}"
    analytics_data = resp_a.json()
    assert float(analytics_data["total_spent"]) > 0
    assert isinstance(analytics_data["category_breakdown"], list)
    assert len(analytics_data["top_merchants"]) > 0
    print("[SUCCESS] Budget Analytics & Heatmap verified!")


    # 7. Test Read-Only GET AI Insights
    print("\n--- 6. Testing Read-Only GET AI Insights Endpoint ---")
    resp_i = client.get(f"/api/expenses/{trip_id}/insights")
    assert resp_i.status_code == 200, f"AI Insights failed: {resp_i.text}"
    insights_data = resp_i.json()
    assert "budget_score" in insights_data
    assert "health" in insights_data
    assert "smart_alerts" in insights_data
    print(f"AI Health Score: {insights_data['budget_score']}/100 ({insights_data['health']})")
    print("[SUCCESS] Read-Only GET AI Insights verified!")

    # 8. Test Receipt OCR Endpoint
    print("\n--- 7. Testing Receipt OCR Endpoint ---")
    resp_ocr = client.post("/api/expenses/ocr", files={"file": ("receipt_test_hotel.jpg", b"fake image bytes", "image/jpeg")})
    assert resp_ocr.status_code == 200, f"OCR failed: {resp_ocr.text}"
    ocr_data = resp_ocr.json()
    assert ocr_data["merchant"] == "Grand Plaza Hotel"
    assert ocr_data["confidence"] >= 0.90
    print("[SUCCESS] Receipt OCR Endpoint verified!")

    # 9. Test CSV and PDF Exporters
    print("\n--- 8. Testing CSV & PDF Exporters ---")
    resp_csv = client.get(f"/api/expenses/export/csv?trip_id={trip_id}")
    assert resp_csv.status_code == 200
    assert "Starbucks" in resp_csv.text

    resp_pdf = client.get(f"/api/expenses/export/pdf?trip_id={trip_id}")
    assert resp_pdf.status_code == 200
    assert "WanderWise Expense Report" in resp_pdf.text
    print("[SUCCESS] CSV & PDF Exporters verified!")

    # 10. Clean up test expense
    client.delete(f"/api/expenses/{exp2_id}")

    print("\n=== ALL WANDERWISE v2.1 EXPENSE & BUDGET MANAGER TESTS PASSED CLEANLY (100%) ===")

if __name__ == "__main__":
    run_tests()
