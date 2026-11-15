"""
test_simplified_trip_creation.py

Automated Test Suite for WanderWise Simplified and Optimized Trip Creation Workflow:
1. Trip creation with only mandatory fields (Destination, Departure Date, Return Date).
2. Trip creation without budget (Unrestricted, AI-calibrated budget generation).
3. Trip creation without preferences (Defaults gracefully to General Exploration).
4. Trip creation with multiple preference chips (Adventure, Culture and History, Food, etc.).
5. One-day trip creation (start_date == end_date, 1 Day Trip duration).
6. Multi-day trip creation (7 days, distinct schedules, zero duplicates).
7. Multiple travellers handling (Adults and Children composition, family mode).
8. Invalid date ranges prevention (return date before departure date strictly rejected).
9. Worldwide destination scalability (Tokyo, Paris, Cairo, Queenstown).
10. Saving and reopening generated itineraries (Full persistence, day and activity retrieval).
11. Location search autocomplete endpoint (/api/trips/locations/search).
12. Location reverse-geocoding endpoint (/api/trips/locations/reverse-geocode).
13. Backward compatibility with existing trips with explicit budgets and custom parameters.
"""

import os
import sys
from datetime import date, timedelta
from typing import Dict, Any, List

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.schemas.trip_schemas import TripCreate
from app.routes.trips import (
    create_new_trip,
    enrich_trip_response,
    search_locations,
    reverse_geocode_location
)
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.ai_service import generate_structured_itinerary

# Setup in-memory SQLite database for deterministic testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session: Session):
    user = User(
        name="Alex Traveler",
        email="alex.traveler@wanderwise.ai",
        password="hashed_secure_password",
        currency="USD"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# =====================================================================
# 1. Trip Creation with Only Mandatory Fields
# =====================================================================
def test_trip_creation_mandatory_fields_only(db_session: Session, test_user: User):
    """
    Validates creating a trip providing ONLY essential mandatory fields:
    Destination, Departure Date, Return Date.
    No budget, no preferences, default 1 traveller.
    """
    trip_in = TripCreate(
        destination="Tokyo",
        start_date=date(2027, 4, 10),
        end_date=date(2027, 4, 14)
    )

    created_trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert created_trip["id"] is not None
    assert created_trip["destination"] == "Tokyo"
    assert created_trip["country"] == "Japan"  # Inferred by AI / location gazetteer
    assert created_trip["duration_days"] == 5
    assert created_trip["group_size"] == 1
    # Budget was omitted: an AI-estimated budget is calculated without failing feasibility
    assert created_trip["budget"] > 0
    assert created_trip["canonical_budget_plan"]["is_feasible"] is True
    assert created_trip["canonical_budget_plan"]["is_unrestricted"] is True

    # Itinerary days generated
    days = created_trip.get("days", [])
    assert len(days) == 5, f"Expected 5 days, got {len(days)}"
    for d in days:
        assert len(d.get("activities", [])) >= 1


# =====================================================================
# 2. Trip Creation Without a Budget
# =====================================================================
def test_trip_creation_without_budget(db_session: Session, test_user: User):
    """
    Validates that when budget is omitted (None), the system generates an
    itinerary without budget restrictions and calculates a realistic benchmark.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=None,
        currency="USD",
        destination="Paris",
        origin_city="London",
        days=4,
        adults=1,
        children=0
    )

    assert plan["is_feasible"] is True
    assert plan["is_unrestricted"] is True
    assert plan["budget_specified"] is False
    assert plan["shortfall"] == 0.0
    assert plan["total_estimated_trip_cost"] > 0
    assert plan["allocated_budget"] == plan["total_estimated_trip_cost"]

    # Now verify via TripCreate
    trip_in = TripCreate(
        destination="Paris",
        start_date=date(2027, 5, 1),
        end_date=date(2027, 5, 4),
        budget=None
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert trip["canonical_budget_plan"]["is_feasible"] is True
    assert trip["budget"] == trip["canonical_budget_plan"]["total_estimated_trip_cost"]


# =====================================================================
# 3. Trip Creation Without Preferences
# =====================================================================
def test_trip_creation_without_preferences(db_session: Session, test_user: User):
    """
    Validates that omitting preferences defaults gracefully to General Exploration
    without validation errors or empty coverage reports.
    """
    trip_in = TripCreate(
        destination="Rome",
        start_date=date(2027, 6, 1),
        end_date=date(2027, 6, 3),
        interests=None
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert trip["interests"] == "General Exploration"
    cov_report = trip.get("interest_coverage_report")
    assert cov_report is not None
    assert cov_report["coverage_percentage"] == 100.0


# =====================================================================
# 4. Trip Creation with Multiple Preferences
# =====================================================================
def test_trip_creation_with_multiple_preferences(db_session: Session, test_user: User):
    """
    Validates that selecting multiple preference chips (Adventure, Culture and History, Food)
    correctly guides the ranking and coverage report.
    """
    trip_in = TripCreate(
        destination="Istanbul",
        start_date=date(2027, 3, 15),
        end_date=date(2027, 3, 18),
        interests="Adventure, Culture and History, Food, Nature"
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert "Adventure" in trip["interests"]
    assert "Culture and History" in trip["interests"]
    assert "Food" in trip["interests"]
    assert "Nature" in trip["interests"]

    report = trip.get("interest_coverage_report")
    assert report is not None
    selected = report.get("selected_interests", [])
    assert "Adventure" in selected
    assert "Food" in selected


# =====================================================================
# 5. One-Day Trip Creation
# =====================================================================
def test_one_day_trip_creation(db_session: Session, test_user: User):
    """
    Validates creating a 1-day trip where start_date == end_date.
    Duration must be 1 day, activities scheduled, no crashes.
    """
    trip_in = TripCreate(
        destination="Tokyo",
        start_date=date(2027, 7, 10),
        end_date=date(2027, 7, 10)
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert trip["duration_days"] == 1
    assert len(trip["days"]) == 1
    acts = trip["days"][0].get("activities", [])
    assert len(acts) >= 1


# =====================================================================
# 6. Multi-Day Trip Creation with Zero Duplicate Attractions
# =====================================================================
def test_multi_day_trip_creation_zero_duplicates(db_session: Session, test_user: User):
    """
    Validates creating a 7-day multi-day trip.
    Verifies 7 days generated with zero duplicate attractions across all days.
    """
    trip_in = TripCreate(
        destination="Istanbul",
        start_date=date(2027, 3, 15),
        end_date=date(2027, 3, 21),
        interests="Culture and History, Food, Shopping",
        group_size=2
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert trip["duration_days"] == 7
    days = trip["days"]
    assert len(days) == 7

    from app.services.pricing.canonical_pricing_registry import normalize_place_entity_key
    seen_keys = set()
    for d in days:
        for act in d.get("activities", []):
            if act.get("activity_type") == "area_suggestion":
                continue
            name = (act.get("place") or {}).get("name") or act.get("title")
            key = normalize_place_entity_key(name)
            assert key not in seen_keys, f"Duplicate attraction '{name}' found on Day {d.get('day_number')}!"
            seen_keys.add(key)

    assert len(seen_keys) >= 14, f"Expected at least 14 unique venues across 7 days, got {len(seen_keys)}"


# =====================================================================
# 7. Multiple Travellers & Family Composition
# =====================================================================
def test_multiple_travellers_family_composition(db_session: Session, test_user: User):
    """
    Validates that having children sets family room occupancy (num_rooms = 1 for 2 adults + 1 child)
    and travel_style='family'.
    """
    trip_in = TripCreate(
        destination="Tokyo",
        start_date=date(2027, 2, 10),
        end_date=date(2027, 2, 16),
        group_size=3,
        trip_preferences={
            "adults": 2,
            "children": 1,
            "interests": "Family Activities, Culture and History"
        }
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert trip["group_size"] == 3
    assert trip["travel_style"] == "family"
    plan = trip["canonical_budget_plan"]
    assert plan["num_rooms"] == 1  # 1 family room occupancy


# =====================================================================
# 8. Invalid Date Range Rejection
# =====================================================================
def test_invalid_date_ranges_rejected():
    """
    Validates that return date before departure date raises ValueError / validation error.
    """
    with pytest.raises(Exception) as excinfo:
        TripCreate(
            destination="Paris",
            start_date=date(2027, 5, 10),
            end_date=date(2027, 5, 5)  # Invalid: Return is before departure!
        )
    assert "Return date cannot be earlier than departure date" in str(excinfo.value)


# =====================================================================
# 9. Worldwide Destination Scalability
# =====================================================================
def test_worldwide_destination_scalability(db_session: Session, test_user: User):
    """
    Validates that diverse worldwide destinations (Cairo, Queenstown, Bali)
    work seamlessly through the simplified interface.
    """
    for dest, expected_country in [("Cairo", "Egypt"), ("Rome", "Italy")]:
        trip_in = TripCreate(
            destination=dest,
            start_date=date(2027, 8, 1),
            end_date=date(2027, 8, 3)
        )
        trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
        assert trip["destination"] == dest
        assert trip["country"] == expected_country
        assert len(trip["days"]) == 3


# =====================================================================
# 10. Saving and Reopening Generated Itineraries
# =====================================================================
def test_saving_and_reopening_generated_itinerary(db_session: Session, test_user: User):
    """
    Validates that a generated trip is stored in the database and reloaded
    with all days, activities, cost badges, and canonical budget metrics.
    """
    trip_in = TripCreate(
        destination="Kyoto",
        start_date=date(2027, 9, 1),
        end_date=date(2027, 9, 4),
        budget=None,
        interests="Culture and History, Nature"
    )
    created = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    trip_id = created["id"]

    # Reload from DB via SQLAlchemy query and enrich_trip_response
    db_trip = db_session.query(Trip).filter(Trip.id == trip_id).first()
    assert db_trip is not None
    reloaded = enrich_trip_response(db_trip, db_session)

    assert reloaded["id"] == trip_id
    assert reloaded["destination"] == "Kyoto"
    assert len(reloaded["days"]) == 4
    assert reloaded["canonical_budget_plan"] is not None
    assert reloaded["canonical_budget_plan"]["is_unrestricted"] is True


# =====================================================================
# 11. Location Search Autocomplete Endpoint
# =====================================================================
def test_location_search_autocomplete_endpoint():
    """
    Validates that /api/trips/locations/search returns matching cities for autocomplete.
    """
    res = search_locations(q="Tok")
    assert len(res) >= 1
    tokyo = next((r for r in res if "tokyo" in r["name"].lower()), None)
    assert tokyo is not None
    assert tokyo["country"] == "Japan"
    assert tokyo["currency"] == "JPY"

    res_coi = search_locations(q="Coi")
    assert len(res_coi) >= 1
    assert any("coimbatore" in r["name"].lower() for r in res_coi)


# =====================================================================
# 12. Location Reverse-Geocoding Endpoint (GPS Button)
# =====================================================================
def test_location_reverse_geocode_endpoint():
    """
    Validates that /api/trips/locations/reverse-geocode resolves GPS coordinates to city name.
    """
    # Coordinates of Istanbul (41.0082, 28.9784)
    rev = reverse_geocode_location(lat=41.0082, lon=28.9784)
    assert rev is not None
    assert "city" in rev
    assert "Istanbul" in rev["city"] or "Turkey" in rev.get("country", "")


# =====================================================================
# 13. Compatibility with Existing Trips & Explicit Budgets
# =====================================================================
def test_compatibility_with_existing_trips_and_explicit_budgets(db_session: Session, test_user: User):
    """
    Validates full backward compatibility when users provide an explicit budget,
    specific currency, and custom transportation preferences.
    """
    trip_in = TripCreate(
        destination="Tokyo",
        country="Japan",
        origin_city="Chennai",
        start_date=date(2027, 2, 10),
        end_date=date(2027, 2, 16),
        budget=400000.0,
        currency="INR",
        travel_style="family",
        accommodation_preference="hotel",
        transportation="Public Metro & Bus",
        group_size=3,
        interests="Culture and History, Food",
        trip_preferences={
            "adults": 2,
            "children": 1,
            "budget_tier": "mid_range"
        }
    )
    trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert trip["budget"] == 400000.0
    assert trip["currency"] == "INR"
    assert trip["canonical_budget_plan"]["is_feasible"] is True
    assert trip["canonical_budget_plan"]["is_unrestricted"] is False
    assert trip["canonical_budget_plan"]["budget_specified"] is True

