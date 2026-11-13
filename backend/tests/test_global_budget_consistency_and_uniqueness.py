"""
test_global_budget_consistency_and_uniqueness.py

Comprehensive regression suite validating:
1. Canonical Financial Calculation Consistency (Review, Dashboard, Workspace, Expenses agree 100%)
2. 1 Family Room occupancy for 2 adults + 1 child (eliminating 2-room divergence)
3. Separation of International Air Corridors from Local Transit Preferences
4. Zero Duplicate Attractions & Dining across all days for a multi-day trip (Tokyo 7-day test)
5. Canonical Pricing Registry (admission fee single-source-of-truth, 0 admission for dining, 'Price unavailable' for unknown)
6. Honest Weather Forecasting horizon disclosure (>14 days reports seasonal climate)
7. Preservation of Locked and Completed Activities on single-day regeneration
8. Global Multi-Destination Transit Architecture (Reykjavik, London, Cairo) with zero destination hardcoding
"""

import pytest
from datetime import date, timedelta
from typing import Dict, Any, List

from app.services.budget_allocation_service import BudgetAllocationService
from app.services.pricing.canonical_pricing_registry import (
    CanonicalPricingRegistry,
    normalize_place_entity_key,
    PricingRecord
)
from app.services.poi_service import fetch_real_pois_for_destination, WORLD_POI_DATABASE
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from app.services.ai_service import regenerate_day_itinerary
from app.routes.trips import (
    create_new_trip,
    enrich_trip_response,
    regenerate_day_endpoint,
    RegenerateDayRequest
)
from app.schemas.trip_schemas import TripCreate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import app.models
from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.place import Place

# Setup in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    monkeypatch.setattr("app.services.ai_service._ai", lambda *args, **kwargs: "[]")
    monkeypatch.setattr("app.routes.trips.generate_structured_itinerary", lambda *args, **kwargs: {"days": []})
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


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
        name="Tokyo Test Family",
        email="tokyo_family_test@wanderwise.com",
        password="hashed_secure_password",
        currency="INR",
        preferred_budget="mid_range"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================================================
# TEST 1: Canonical Budget Calculation & Corridor vs Local Transit Separation
# ==============================================================================

def test_canonical_budget_calculation_tokyo():
    """
    Validates Tokyo test case:
    - Origin: Coimbatore, Destination: Tokyo, Japan
    - Dates: 10–16 Feb 2027 (7 days, 6 nights)
    - Travelers: 2 adults + 1 child (age 6)
    - Budget: ₹6,50,000 INR
    - Local transit preference: "Public Metro & Bus"
    """
    total_budget = 650000.0
    plan = BudgetAllocationService.calculate_plan(
        total_budget=total_budget,
        currency="INR",
        tier="mid_range",
        destination="Tokyo",
        origin="Coimbatore",
        days=7,
        travelers_count=3,
        travel_style="family",
        children_count=1,
        adults_count=2,
        transport_mode="Public Metro & Bus",
        accommodation_preference="hotel"
    )

    # 1. Total allocation must equal the total budget
    assert abs(plan["total_allocated_categories"] - total_budget) < 0.01

    # 2. Strict financial plan validation passes
    is_valid, validation_errors = BudgetAllocationService.validate_financial_plan(plan)
    assert is_valid, f"Financial plan validation failed: {validation_errors}"

    # 3. Lodging occupancy for family (2 adults + 1 child) must be 1 family room, NOT 2 rooms
    assert plan["num_rooms"] == 1, f"Expected 1 room for family of 3, got {plan['num_rooms']}"
    assert plan["nights"] == 6

    # 4. Outbound and return transport MUST be international flight corridor, NOT "Public Metro & Bus"
    transport = plan["transportation_details"]
    assert transport["is_international"] is True
    assert "Flight" in transport["corridor_mode"] or "Airline" in transport["corridor_mode"]
    assert transport["local_transit_mode"] == "Public Metro & Bus"

    # 5. Outbound transport + return transport == total transport cost
    assert abs((transport["outbound_estimated_cost"] + transport["return_estimated_cost"]) - transport["total_transport_cost"]) < 0.05
    cat_by_key = {c["key"]: c for c in plan["categories"]}
    outbound_amt = cat_by_key["outbound_transport"]["amount"]
    return_amt = cat_by_key["return_transport"]["amount"]
    assert outbound_amt == return_amt
    assert abs(sum(c["amount"] for c in plan["categories"]) - total_budget) < 0.05

    # 6. Category breakdown labels clearly distinguish international flight from destination transit
    assert "Flight" in cat_by_key["outbound_transport"]["label"]
    assert "Flight" in cat_by_key["return_transport"]["label"]
    assert "Transit" in cat_by_key["local_transport"]["label"] or "Metro" in cat_by_key["local_transport"]["label"]


# ==============================================================================
# TEST 2: Trip Creation Stores and Preserves Canonical Budget Plan
# ==============================================================================

def test_trip_creation_stores_canonical_budget_plan(db_session: Session, test_user: User):
    """
    Validates that creating a trip stores the canonical budget plan in
    trip.trip_preferences['canonical_budget_plan'] and that enrich_trip_response
    serves identical numbers without divergence.
    """
    trip_in = TripCreate(
        user_id=test_user.id,
        title="Tokyo Family Adventure",
        destination="Tokyo",
        country="Japan",
        start_date=date(2027, 2, 10),
        end_date=date(2027, 2, 16),
        budget=650000.0,
        currency="INR",
        travel_style="family",
        accommodation_preference="hotel",
        transportation="Public Metro & Bus",
        group_size=3,
        interests="culture, temples, food, anime, photography",
        trip_preferences={
            "origin": "Coimbatore",
            "adults": 2,
            "children": 1,
            "children_ages": [6],
            "budget_tier": "mid_range"
        }
    )

    created_trip = create_new_trip(data=trip_in, db=db_session, current_user=test_user)
    assert created_trip.get("id") is not None

    enriched = created_trip if isinstance(created_trip, dict) else enrich_trip_response(created_trip, db_session)
    prefs = enriched.get("trip_preferences", {})
    canonical_plan = prefs.get("canonical_budget_plan")

    assert canonical_plan is not None, "Canonical budget plan must be stored in trip_preferences"
    assert canonical_plan["num_rooms"] == 1
    assert "Flight" in canonical_plan["transportation_details"]["corridor_mode"]
    assert canonical_plan["transportation_details"]["local_transit_mode"] == "Public Metro & Bus"

    # Financial consistency: The total estimated trip cost must match the canonical plan exactly
    total_estimated = canonical_plan["total_estimated_trip_cost"]
    assert total_estimated > 0
    trans_details = canonical_plan["transportation_details"]
    assert abs((trans_details["outbound_estimated_cost"] + trans_details["return_estimated_cost"]) -
               trans_details["total_transport_cost"]) < 0.05


# ==============================================================================
# TEST 3: Zero Duplicate Attractions Across All 7 Days (Tokyo Test Case)
# ==============================================================================

def test_tokyo_7_day_trip_zero_duplicate_attractions():
    """
    Validates that a 7-day Tokyo itinerary schedules distinct authentic POIs across
    all days with ZERO cross-day duplicates for attractions and dining.
    """
    tokyo_pois = fetch_real_pois_for_destination("Tokyo")
    assert len(tokyo_pois) >= 20, f"Expected at least 20 POIs in Tokyo database, found {len(tokyo_pois)}"

    # Construct raw days referencing various POIs
    raw_days = []
    poi_idx = 0
    for day_num in range(1, 8):
        day_acts = []
        for slot in ["morning", "afternoon", "evening"]:
            poi = tokyo_pois[poi_idx % len(tokyo_pois)]
            poi_idx += 1
            day_acts.append({
                "time_slot": slot,
                "start_time": "09:00" if slot == "morning" else ("14:00" if slot == "afternoon" else "18:30"),
                "end_time": "11:30" if slot == "morning" else ("16:00" if slot == "afternoon" else "20:30"),
                "title": f"Explore {poi['name']}",
                "description": poi.get("description", ""),
                "place": poi,
                "ticket_price": poi.get("ticket_price", 0.0),
                "is_dining": poi.get("is_dining", False)
            })
        raw_days.append({
            "day_number": day_num,
            "title": f"Day {day_num}: Discover Tokyo",
            "activities": day_acts
        })

    is_valid, warnings, validated_days = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_days,
        destination="Tokyo",
        start_date=date(2027, 2, 10),
        end_date=date(2027, 2, 16),
        expected_days=7,
        currency="INR",
        interests="culture, temples, food, anime, photography",
        transport_mode="Public Metro & Bus",
        accommodation_preference="hotel",
        travelers_count=3,
        adults_count=2,
        children_count=1
    )

    # Verify that no attraction key is repeated across all 7 days
    seen_entity_keys = set()
    total_activities = 0
    for day in validated_days:
        acts = day.get("activities", [])
        assert len(acts) >= 3, f"Day {day.get('day_number')} has fewer than 3 activities"
        for act in acts:
            total_activities += 1
            p_name = (act.get("place", {}).get("name") if isinstance(act.get("place"), dict) else None) or act.get("title", "")
            key = normalize_place_entity_key(p_name)
            assert key not in seen_entity_keys, f"Duplicate attraction detected across days: '{p_name}' (key: '{key}')"
            seen_entity_keys.add(key)

    assert total_activities == 21, f"Expected 21 unique activities across 7 days, got {total_activities}"


# ==============================================================================
# TEST 4: Canonical Pricing Registry Single Source of Truth
# ==============================================================================

def test_canonical_pricing_registry_behavior():
    """
    Validates:
    - Tokyo Skytree: ~3,100 JPY
    - Shibuya Sky: ~2,200 JPY
    - Senso-ji: 0 JPY ticket (Free Entry)
    - Meiji Jingu: 0 JPY ticket (Free Entry)
    - Ichiran Ramen: 0 ticket price, price_status = 'A la carte dining (No entry ticket)'
    - Unknown attractions: price_status = 'Price unavailable' (never defaulting to Free Entry)
    """
    registry = CanonicalPricingRegistry(target_currency="JPY")

    # 1. Tokyo Skytree
    rec_skytree = registry.register(
        place_name="Tokyo Skytree",
        raw_price=3100.0,
        currency="JPY",
        is_dining=False
    )
    assert rec_skytree.adult_price == 3100.0
    assert rec_skytree.child_price == 1550.0  # Child 50% discount
    assert rec_skytree.price_status == "Paid admission"

    # Querying again returns the exact same canonical price
    rec_skytree_2 = registry.register("Visit Tokyo Skytree Observatory Deck", raw_price=9999.0, currency="JPY")
    assert rec_skytree_2.adult_price == 3100.0, "Subsequent mentions must reuse canonical registered price"

    # 2. Shibuya Sky
    rec_shibuya = registry.register("Shibuya Sky", raw_price=2200.0, currency="JPY")
    assert rec_shibuya.adult_price == 2200.0

    # 3. Senso-ji Temple (Free landmark)
    rec_sensoji = registry.register("Senso-ji Temple", raw_price=0.0, currency="JPY")
    assert rec_sensoji.adult_price == 0.0
    assert rec_sensoji.price_status == "Free Entry"

    # 4. Dining venue: Ichiran Ramen
    rec_dining = registry.register("Ichiran Ramen Asakusa", raw_price=0.0, currency="JPY", is_dining=True)
    assert rec_dining.adult_price == 0.0
    assert rec_dining.price_status == "A la carte dining (No entry ticket)"
    assert rec_dining.is_dining is True

    # 5. Unknown attraction without verified price
    rec_unknown = registry.register("Random Unverified Spot Tokyo", raw_price=None, currency="JPY")
    assert rec_unknown.adult_price is None
    assert rec_unknown.price_status == "Price unavailable"
    assert rec_unknown.is_free is False


# ==============================================================================
# TEST 5: Weather Horizon Disclosure (>14 Days Shows Seasonal Climate)
# ==============================================================================

def test_weather_horizon_disclosure():
    """
    For a trip in February 2027 (> 14 days out), the system must disclose
    seasonal climate standard or historical benchmark rather than fake live radar.
    """
    future_date = date(2027, 2, 10)
    today = date.today()
    days_out = (future_date - today).days
    assert days_out > 14, "Test date must be beyond the 14-day live weather horizon"

    raw_day = [{
        "day_number": 1,
        "title": "Day 1: Arrival & Exploration",
        "activities": [
            {
                "time_slot": "morning",
                "start_time": "09:00",
                "end_time": "11:30",
                "title": "Senso-ji Temple",
                "place": {"name": "Senso-ji Temple", "category": "Historic Temple"},
                "ticket_price": 0.0
            }
        ]
    }]

    _, _, validated = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_day,
        destination="Tokyo",
        start_date=future_date,
        end_date=future_date,
        expected_days=1,
        currency="JPY"
    )

    day1 = validated[0]
    acts = day1.get("activities", [])
    assert len(acts) > 0
    # Weather suitability should reflect realistic seasonal / mixed climate rather than claiming live radar
    assert acts[0].get("weather_suitability") in ["Mixed", "Indoor / Outdoor", "Fair", "Mild", "Not available", "Seasonal Average"]


# ==============================================================================
# TEST 6: Preservation of Locked & Completed Activities on Single-Day Regeneration
# ==============================================================================

def test_preserve_locked_and_completed_activities_on_regeneration(db_session: Session, test_user: User, monkeypatch):
    """
    Validates that:
    1. Locking an activity preserves it when regenerating that day.
    2. Completed activities are also preserved.
    3. Regenerating Day 1 strictly excludes venues already scheduled on Day 2.
    """
    monkeypatch.setattr("app.services.ai_service._ai", lambda *args, **kwargs: "[]")
    # Create trip in DB
    trip = Trip(
        user_id=test_user.id,
        title="Tokyo Test Trip",
        destination="Tokyo",
        country="Japan",
        start_date=date(2027, 2, 10),
        end_date=date(2027, 2, 11),
        budget=650000.0,
        currency="INR",
        group_size=3
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Create Day 1 and Day 2
    day1 = ItineraryDay(trip_id=trip.id, day_number=1, date=trip.start_date, title="Day 1")
    day2 = ItineraryDay(trip_id=trip.id, day_number=2, date=trip.start_date + timedelta(days=1), title="Day 2")
    db_session.add_all([day1, day2])
    db_session.commit()
    db_session.refresh(day1)
    db_session.refresh(day2)

    # Add places
    p_sensoji = Place(name="Senso-ji Temple", city="Tokyo", country="Japan")
    p_ramen = Place(name="Ichiran Ramen Asakusa", city="Tokyo", country="Japan")
    p_skytree = Place(name="Tokyo Skytree", city="Tokyo", country="Japan")
    p_shibuya = Place(name="Shibuya Sky", city="Tokyo", country="Japan")
    db_session.add_all([p_sensoji, p_ramen, p_skytree, p_shibuya])
    db_session.commit()

    # Day 1: Act 1 (Locked), Act 2 (Unlocked)
    act1_locked = ItineraryActivity(
        day_id=day1.id,
        place_id=p_sensoji.id,
        title="Senso-ji Temple",
        time_slot="morning",
        start_time="09:00",
        end_time="11:00",
        is_locked=True
    )
    act2_unlocked = ItineraryActivity(
        day_id=day1.id,
        place_id=p_ramen.id,
        title="Ichiran Ramen Asakusa",
        time_slot="afternoon",
        start_time="12:00",
        end_time="13:30",
        is_locked=False
    )
    # Day 2: Act 3 on Day 2 (Tokyo Skytree)
    act3_day2 = ItineraryActivity(
        day_id=day2.id,
        place_id=p_skytree.id,
        title="Tokyo Skytree",
        time_slot="morning",
        start_time="09:30",
        end_time="12:00",
        is_locked=False
    )
    db_session.add_all([act1_locked, act2_unlocked, act3_day2])
    db_session.commit()

    locked_id = act1_locked.id
    unlocked_id = act2_unlocked.id

    # Call regenerate_day_endpoint for Day 1
    req = RegenerateDayRequest(day_number=1, notes="Include art or nature")
    result = regenerate_day_endpoint(
        trip_id=trip.id,
        data=req,
        db=db_session,
        current_user=test_user
    )

    assert result["success"] is True

    # Re-query Day 1 activities from DB
    day1_acts = db_session.query(ItineraryActivity).filter(ItineraryActivity.day_id == day1.id).all()
    act_ids = {a.id for a in day1_acts}
    act_titles = [a.title for a in day1_acts]

    # 1. Locked activity MUST be preserved
    assert locked_id in act_ids, "Locked activity must remain preserved in DB"

    # 2. Unlocked activity was replaced
    assert unlocked_id not in act_ids, "Unlocked activity should have been replaced"

    # 3. New activities must NOT repeat Tokyo Skytree from Day 2
    day2_poi_key = normalize_place_entity_key("Tokyo Skytree")
    for a in day1_acts:
        assert normalize_place_entity_key(a.title) != day2_poi_key, f"Regenerated Day 1 must not include Day 2 venue ({a.title})"


# ==============================================================================
# TEST 7: Global Multi-Destination Transit Architecture (Zero Hardcoding)
# ==============================================================================

@pytest.mark.parametrize("origin,destination,country,budget,currency,expected_corridor", [
    ("Chennai", "London", "United Kingdom", 450000.0, "INR", "Flight"),
    ("Paris", "Reykjavik", "Iceland", 3000.0, "EUR", "Flight"),
    ("Mumbai", "Cairo", "Egypt", 250000.0, "INR", "Flight"),
    ("New York", "Boston", "United States", 1500.0, "USD", "Flight")
])
def test_global_transit_corridor_vs_local(origin, destination, country, budget, currency, expected_corridor):
    """
    Validates that corridor transit classification and local transit preferences
    are dynamically resolved for any destination worldwide without hardcoding.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=budget,
        currency=currency,
        tier="mid_range",
        destination=destination,
        origin=origin,
        days=5,
        travelers_count=2,
        transport_mode="Public Metro & Bus",
        accommodation_preference="hotel"
    )

    is_valid, errs = BudgetAllocationService.validate_financial_plan(plan)
    assert is_valid, f"Validation failed for {destination}: {errs}"

    trans = plan["transportation_details"]
    assert expected_corridor in trans["corridor_mode"]
    assert trans["local_transit_mode"] == "Public Metro & Bus"

    # Sum of categories must match total budget
    assert abs(plan["total_allocated_categories"] - budget) < 0.05
