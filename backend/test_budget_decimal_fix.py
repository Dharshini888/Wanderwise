import os
import sys
from decimal import Decimal

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense
from app.services.trip_service import to_decimal, calculate_trip_metrics, enrich_trip_response, get_dashboard_widgets


def test_budget_decimal_calculations():
    print("=== STARTING BUDGET DECIMAL FIX VERIFICATION ===")

    # 1. Test to_decimal Helper Function
    print("\n--- 1. Testing to_decimal Helper Function ---")
    assert to_decimal(None) == Decimal("0")
    assert to_decimal(100.5) == Decimal("100.5")
    assert to_decimal("250.75") == Decimal("250.75")
    assert to_decimal(Decimal("500.00")) == Decimal("500.00")
    assert to_decimal(0) == Decimal("0")
    print("[SUCCESS] to_decimal helper verified for all types and None!")

    # 2. Setup DB Session & Mock Data
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User(email="decimal_test@wanderwise.ai", password_hash="hashed", full_name="Decimal Test User")
            db.add(user)
            db.commit()
            db.refresh(user)

        # 3. Test calculate_trip_metrics with Float budget & Decimal expenses
        print("\n--- 2. Testing calculate_trip_metrics with Float budget & Decimal expenses ---")
        trip_float = Trip(
            user_id=user.id,
            destination="Paris",
            country="France",
            start_date="2026-08-01",
            end_date="2026-08-05",
            budget=2000.0, # Float
            currency="EUR"
        )
        db.add(trip_float)
        db.commit()
        db.refresh(trip_float)

        exp1 = Expense(
            trip_id=trip_float.id,
            title="Eiffel Tower Ticket",
            amount=Decimal("45.50"), # Decimal
            category="ACTIVITIES",
            currency="EUR",
            expense_date="2026-08-01"
        )
        exp2 = Expense(
            trip_id=trip_float.id,
            title="Bistro Lunch",
            amount=Decimal("120.75"), # Decimal
            category="FOOD",
            currency="EUR",
            expense_date="2026-08-01"
        )
        db.add(exp1)
        db.add(exp2)
        db.commit()

        # This call previously raised TypeError: unsupported operand type(s) for -: 'float' and 'decimal.Decimal'
        metrics = calculate_trip_metrics(trip_float, db)
        assert metrics["total_budget_remaining"] == 1833.75, f"Expected 1833.75, got {metrics['total_budget_remaining']}"
        assert metrics["estimated_daily_budget"] == 400.0
        assert metrics["budget_per_person"] == 2000.0
        print("[SUCCESS] calculate_trip_metrics float vs Decimal calculation passed cleanly!")

        # 4. Test calculate_trip_metrics with None budget and None expenses
        print("\n--- 3. Testing calculate_trip_metrics with None budget & None expenses ---")
        trip_none = Trip(
            user_id=user.id,
            destination="Rome",
            country="Italy",
            start_date="2026-09-01",
            end_date="2026-09-03",
            budget=0.0,
            currency="EUR"
        )
        db.add(trip_none)
        db.commit()
        db.refresh(trip_none)
        
        # Test in-memory trip with None budget
        trip_none.budget = None

        metrics_none = calculate_trip_metrics(trip_none, db)
        assert metrics_none["total_budget_remaining"] == 0.0
        assert metrics_none["estimated_daily_budget"] == 0.0
        print("[SUCCESS] calculate_trip_metrics with NULL budget passed cleanly!")

        # 5. Test enrich_trip_response
        print("\n--- 4. Testing enrich_trip_response ---")
        enriched = enrich_trip_response(trip_float, db)
        assert enriched["total_budget_remaining"] == 1833.75
        assert enriched["budget"] == 2000.0
        print("[SUCCESS] enrich_trip_response returned correct metrics!")

        # 6. Test get_dashboard_widgets
        print("\n--- 5. Testing get_dashboard_widgets ---")
        widgets = get_dashboard_widgets(db, user.id)
        assert "budget_remaining" in widgets
        assert isinstance(widgets["budget_remaining"], float)
        print("[SUCCESS] get_dashboard_widgets executed cleanly with mixed types!")

        # Cleanup test trips
        db.delete(exp1)
        db.delete(exp2)
        db.delete(trip_float)
        db.delete(trip_none)
        db.commit()

        print("\n=== ALL BUDGET DECIMAL FIX VERIFICATION TESTS PASSED (100%) ===")
    finally:
        db.close()

if __name__ == "__main__":
    test_budget_decimal_calculations()
