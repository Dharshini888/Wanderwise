import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database.connection import SessionLocal, engine, Base
from app.models.trip import Trip
from app.models.budget import Budget
from app.models.user import User
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.schemas.trip_schemas import TripCreate
from app.services.trip_service import create_trip
from app.services.expense_service import get_or_create_budget, sync_budget_metrics
from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.route_optimizer import RouteOptimizer


def test_budget_creation():
    print("\n=======================================================")
    print("TEST 1: BUDGET CREATION & UPSERT TEST")
    print("=======================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Case 1 & 2: Create a test trip and initialize budget
        trip_data = TripCreate(
            user_id=1,
            destination="Hawaii",
            country="United States",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
            budget=5000.0,
            currency="USD",
            interests="Sightseeing"
        )
        trip = create_trip(db, trip_data)
        print(f"[SUCCESS] Created Trip ID: {trip.id}")

        # First request to get_or_create_budget
        b1 = get_or_create_budget(db, trip)
        assert b1 is not None
        assert b1.trip_id == trip.id
        print(f"[SUCCESS] First Budget initialized: ID={b1.id}, trip_id={b1.trip_id}, total_budget={b1.total_budget}")

        # Second request to get_or_create_budget (repeat request)
        b2 = get_or_create_budget(db, trip)
        assert b2 is not None
        assert b2.id == b1.id
        print(f"[SUCCESS] Second Budget request re-used existing row: ID={b2.id}")

        # Verify only 1 budget row exists for this trip_id in DB
        budget_count = db.query(Budget).filter(Budget.trip_id == trip.id).count()
        assert budget_count == 1, f"Expected 1 budget row for trip {trip.id}, found {budget_count}"
        print(f"[SUCCESS] Verified exactly 1 budget row in database for trip {trip.id}")

        # Test sync_budget_metrics idempotency
        sync_budget_metrics(db, trip.id)
        budget_count_after_sync = db.query(Budget).filter(Budget.trip_id == trip.id).count()
        assert budget_count_after_sync == 1
        print(f"[SUCCESS] sync_budget_metrics verified idempotent (still 1 row)")

    finally:
        db.close()


def test_transit_shapes():
    print("\n=======================================================")
    print("TEST 2: TRANSIT OPTIMIZER & SHAPES TEST")
    print("=======================================================")

    # Test RouteOptimizer with None, [], and list of routes
    res_none = RouteOptimizer.optimize(None)
    assert isinstance(res_none, dict)
    print(f"[SUCCESS] RouteOptimizer.optimize(None) returned dict: {res_none}")

    res_empty = RouteOptimizer.optimize([])
    assert isinstance(res_empty, dict)
    print(f"[SUCCESS] RouteOptimizer.optimize([]) returned dict: {res_empty}")

    sample_route = {
        "route_id": "test_1",
        "provider": "OSRM",
        "mode": "Road",
        "origin": "Hawaii",
        "destination": "Honolulu",
        "distance_km": 25.0,
        "duration_min": 30.0,
        "verification_status": "Provider Calculated"
    }
    res_routes = RouteOptimizer.optimize([sample_route])
    assert isinstance(res_routes, dict)
    assert res_routes.get("recommended_route") is not None
    print(f"[SUCCESS] RouteOptimizer.optimize([sample_route]) returned dict with recommended_route")

    # Test TransitOrchestrator plan generation
    plan = TransitOrchestrator.get_transit_plan(
        origin="Tokyo",
        destination="Kyoto",
        preferred_mode="fastest"
    )
    assert isinstance(plan, dict)
    assert "recommended_route" in plan
    print(f"[SUCCESS] TransitOrchestrator.get_transit_plan returned valid response payload with recommended_route key: {type(plan['recommended_route'])}")


if __name__ == "__main__":
    test_budget_creation()
    test_transit_shapes()
    print("\n=======================================================")
    print("ALL BACKEND VERIFICATION TESTS PASSED 100%!")
    print("=======================================================\n")
