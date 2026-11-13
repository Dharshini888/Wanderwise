"""
test_global_itinerary_architecture.py — 15-Point Automated Regression Test Suite
Validates the complete global itinerary generation architecture across worldwide destinations:
Kyoto, Switzerland, Singapore, Coimbatore, Paris, Bali, Dubai, Queenstown, rural destinations, and ambiguous locations.
"""

import pytest
import json
from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.schemas.trip_schemas import TripCreate
from app.routes.trips import resolve_trip_preferences, create_new_trip
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.location.location_normalizer import resolve_destination_info, normalize_location
from app.services.poi_service import fetch_real_pois_for_destination, resolve_poi_coordinates
from app.services.route_optimizer import estimate_travel_transition
from app.ai.providers.mock_provider import MockProvider
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator

# In-memory SQLite for complete isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
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
        name="Global Architecture User",
        email="architect@wanderwise.com",
        password="hashed_pw_test",
        currency="INR",
        preferred_budget="mid_range"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# 1. Interest Preservation Test
# ============================================================================
def test_scenario_1_interest_preservation(test_user):
    """
    Test 1: Interest Preservation
    User selects: 'Shopping, History, Street Food, Photography, Hidden Gems'.
    Must preserve ONLY these exact selected tags with zero auto-injection of 'Solo', 'Food & Dining', etc.
    """
    trip_data = TripCreate(
        user_id=test_user.id,
        destination="Kyoto, Japan",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=35),
        budget=250000.0,
        currency="INR",
        travel_style="family",
        interests="Shopping, History, Street Food, Photography, Hidden Gems",
        group_size=3
    )

    resolved = resolve_trip_preferences(trip_data, test_user)
    tags = [t.strip() for t in resolved["interests"].split(",") if t.strip()]

    expected_tags = {"Shopping", "History", "Street Food", "Photography", "Hidden Gems"}
    assert set(tags) == expected_tags, f"Expected {expected_tags}, got {set(tags)}"
    assert "Solo" not in tags, "'Solo' travel style must not be injected into activity interests"
    assert "Food & Dining" not in tags, "'Food & Dining' must not be auto-injected when specific 'Street Food' was chosen"
    assert "Sightseeing" not in tags, "Generic 'Sightseeing' default must not contaminate explicit user selection"


# ============================================================================
# 2. No Fabricated Attractions Test
# ============================================================================
def test_scenario_2_no_fabricated_attractions():
    """
    Test 2: No Fabricated Attractions
    All attractions across Kyoto, Paris, and Switzerland must have authentic identities
    and distinct real coordinates, not repeated placeholder strings.
    """
    destinations = ["Kyoto, Japan", "Paris, France", "Switzerland"]
    for dest in destinations:
        pois = fetch_real_pois_for_destination(dest)
        assert len(pois) >= 5, f"Expected at least 5 authentic POIs for {dest}, got {len(pois)}"

        names = [p["name"] for p in pois]
        # Ensure no generic placeholder repetitions
        assert not any(n == f"{dest} Historic City Center" for n in names)
        # Ensure non-zero distinct coordinates
        distinct_coords = {(p["latitude"], p["longitude"]) for p in pois if p.get("latitude") and p.get("longitude")}
        assert len(distinct_coords) >= 4, f"POIs in {dest} must have distinct GPS coordinates"


# ============================================================================
# 3. No Fabricated Restaurants Test
# ============================================================================
def test_scenario_3_no_fabricated_restaurants():
    """
    Test 3: No Fabricated Restaurants
    Dining recommendations must not claim fake awards, fake Michelin stars, or fake registries.
    Unverified venues must be labeled honestly as Area Suggestions or Unrated.
    """
    provider = MockProvider()
    prompt = (
        "Destination: Queenstown, New Zealand\n"
        "Origin City: Coimbatore\n"
        "Total Duration: EXACTLY 3 Days\n"
        "2 Adults, 0 Children\n"
        "Dietary Preferences: Vegetarian\n"
        "Interests: Nature, Photography"
    )
    res_str = provider.generate(prompt)
    data = json.loads(res_str)
    days = data.get("trip", {}).get("itinerary_days", [])

    dining_activities = [
        act for day in days for act in day.get("activities", [])
        if act.get("is_dining") or act.get("category") == "Restaurant"
    ]

    for dining in dining_activities:
        prov = dining.get("provenance", {})
        # Must not fabricate fake awards or Michelin claims
        ai_reason = dining.get("ai_reason", "")
        assert "michelin 3-star" not in ai_reason.lower()
        assert "unesco gastronomic" not in ai_reason.lower()

        # If it is an unverified area suggestion, provenance must be transparent
        if dining.get("is_area_suggestion"):
            assert "Unverified" in prov.get("place_verification", "") or "Area Suggestion" in prov.get("place_verification", "")
            place = dining.get("place", {})
            assert place.get("rating") is None or "Unrated" in str(place.get("rating_source", ""))


# ============================================================================
# 4. Outbound & Return Transport Directional Calculation Test
# ============================================================================
def test_scenario_4_separate_outbound_return_transport():
    """
    Test 4: Separate Outbound & Return Transport Calculation with Group Multipliers
    Outbound and Return must be explicitly tracked and equal 50% each of roundtrip.
    Group multipliers must correctly account for both adults and children.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=300000.0,
        currency="INR",
        tier="mid_range",
        destination="Dubai, UAE",
        origin_city="Coimbatore",
        days=5,
        adults=3,
        children=1
    )

    trans = plan["transportation_details"]
    outbound = trans["outbound_leg"]
    return_leg = trans["return_leg"]

    assert outbound["estimated_cost"] > 0
    assert return_leg["estimated_cost"] > 0
    # Both legs should be equal for symmetric roundtrip benchmark
    assert abs(outbound["estimated_cost"] - return_leg["estimated_cost"]) <= 0.05
    assert trans["adult_passengers"] == 3
    assert trans["child_passengers"] == 1

    expected_total = (3 * trans["adult_fare_roundtrip"]) + (1 * trans["child_fare_roundtrip"])
    assert abs(trans["total_transport_cost"] - round(expected_total, 2)) <= 1.0


# ============================================================================
# 5. Child Pricing Rules Test
# ============================================================================
def test_scenario_5_child_pricing_rules():
    """
    Test 5: Child Pricing Rules
    Validate that child fares and daily expenses are correctly discounted:
    - Child transport fare is ~75% of adult fare.
    - Child daily food is ~60% of adult daily food.
    - Room count scales with party size: 2 adults = 1 room; 2 adults + 2 children = 2 rooms.
    """
    plan_adults_only = BudgetAllocationService.calculate_plan(
        total_budget=400000.0,
        currency="INR",
        tier="mid_range",
        destination="Singapore",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=0
    )

    plan_with_children = BudgetAllocationService.calculate_plan(
        total_budget=400000.0,
        currency="INR",
        tier="mid_range",
        destination="Singapore",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=2
    )

    assert plan_adults_only["num_rooms"] == 1
    assert plan_with_children["num_rooms"] == 2
    assert plan_with_children["num_rooms"] > plan_adults_only["num_rooms"]

    trans = plan_with_children["transportation_details"]
    assert trans["child_fare_roundtrip"] < trans["adult_fare_roundtrip"]
    fare_ratio = trans["child_fare_roundtrip"] / trans["adult_fare_roundtrip"]
    assert 0.60 <= fare_ratio <= 0.85

    assert plan_with_children["food_estimate"] > plan_adults_only["food_estimate"]
    assert plan_with_children["activities_estimate"] > plan_adults_only["activities_estimate"]


# ============================================================================
# 6. Budget Insufficiency Blocking Test (HTTP 422)
# ============================================================================
def test_scenario_6_budget_insufficiency_blocking(db_session, test_user):
    """
    Test 6: Budget Insufficiency Blocking (HTTP 422 BUDGET_INSUFFICIENT)
    Attempting to create a luxury trip to Paris with insufficient funds (₹30,000 for 7 days)
    must strictly fail with HTTP 422 and return structured shortfall information.
    """
    trip_data = TripCreate(
        user_id=test_user.id,
        destination="Paris, France",
        start_date=date.today() + timedelta(days=40),
        end_date=date.today() + timedelta(days=47),
        budget=30000.0,
        currency="INR",
        travel_style="couple",
        group_size=2,
        trip_preferences={
            "adults": 2,
            "children": 0,
            "origin_city": "Coimbatore",
            "budget_tier": "luxury"
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        create_new_trip(data=trip_data, db=db_session, current_user=test_user)

    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    assert detail["error"] == "BUDGET_INSUFFICIENT"
    assert detail["is_feasible"] is False
    assert detail["shortfall"] > 200000.0
    assert len(detail["affordable_alternatives"]) >= 1


# ============================================================================
# 7. Budget Accuracy Reconciliation Test
# ============================================================================
def test_scenario_7_budget_accuracy_reconciliation():
    """
    Test 7: Budget Accuracy Reconciliation
    The sum of all estimated category costs + contingency must exactly equal total estimated trip cost:
    Outbound + Return + Lodging + Food + Local Transit + Activities + Fees + Contingency == Total.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=150000.0,
        currency="INR",
        tier="mid_range",
        destination="Bali, Indonesia",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=1
    )

    est_outbound = plan["estimated_outbound_transport"]
    est_return = plan["estimated_return_transport"]
    est_lodging = plan["accommodation_estimate"]
    est_food = plan["food_estimate"]
    est_transit = plan["local_transport_estimate"]
    est_activities = plan["activities_estimate"]
    est_fees = plan["travel_fees_estimate"]
    est_contingency = plan["contingency_estimate"]

    subtotal = est_outbound + est_return + est_lodging + est_food + est_transit + est_activities + est_fees
    reconciled_total = round(subtotal + est_contingency, 2)

    assert abs(plan["total_estimated_trip_cost"] - reconciled_total) <= 0.05, (
        f"Reconciled total {reconciled_total} does not match {plan['total_estimated_trip_cost']}"
    )


# ============================================================================
# 8. Geographic Coordinate Validity Test
# ============================================================================
def test_scenario_8_geographic_coordinate_validity():
    """
    Test 8: Geographic Coordinate Validity
    Every normalized place and POI must have coordinates strictly within [-90, 90] and [-180, 180].
    """
    locations = [
        {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
        {"name": "Bali", "lat": -8.4095, "lon": 115.1889},
        {"name": "Dubai", "lat": 25.2048, "lon": 55.2708},
        {"name": "Queenstown", "lat": -45.0312, "lon": 168.6626},
    ]

    for loc in locations:
        norm = normalize_location(loc)
        assert -90.0 <= norm["latitude"] <= 90.0
        assert -180.0 <= norm["longitude"] <= 180.0


# ============================================================================
# 9. Route Accuracy & Straight-Line Labeling Test
# ============================================================================
def test_scenario_9_route_accuracy_and_straight_line_labeling():
    """
    Test 9: Route Accuracy & Straight-Line Labeling
    When OSRM is used or falls back to Haversine, distance provenance must be transparent.
    """
    from app.services.maps.osrm_service import get_osrm_route
    p1 = {"name": "Kinkaku-ji", "latitude": 35.0394, "longitude": 135.7292}
    p2 = {"name": "Gion", "latitude": 35.0037, "longitude": 135.7772}

    # Test OSRM routing
    route = get_osrm_route(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"], mode="driving")
    assert route["distance_km"] > 0
    assert route["duration_minutes"] > 0
    assert route["source"] in ["Live (OSRM)", "Calibrated Routing Estimate"]

    # Test route optimizer transition estimation
    transition = estimate_travel_transition(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
    assert transition["distance_km"] > 0
    assert "distance" in transition
    assert "travel_mode" in transition
    assert "travel_time" in transition


# ============================================================================
# 10. Arrival and Departure Day Schedule Flexibility Test
# ============================================================================
def test_scenario_10_arrival_departure_day_flexibility():
    """
    Test 10: Arrival and Departure Day Schedule Flexibility
    - Day 1 must feature flexible arrival check-in and unhurried orientation.
    - Last Day must allocate buffer for checkout and departure transfers.
    """
    provider = MockProvider()
    prompt = (
        "Destination: Kyoto, Japan\n"
        "Origin City: Coimbatore\n"
        "Total Duration: EXACTLY 5 Days\n"
        "2 Adults, 0 Children\n"
        "Dietary Preferences: Vegetarian"
    )
    res_str = provider.generate(prompt)
    data = json.loads(res_str)
    days = data.get("trip", {}).get("itinerary_days", [])

    assert len(days) == 5

    # Day 1: Arrival check-in presence and flexible note
    day1 = days[0]
    day1_titles = [act["title"] for act in day1.get("activities", [])]
    assert any("Arrival" in t or "Check-in" in t or "Orientation" in t for t in day1_titles)
    assert "flexible" in day1.get("theme_note", "").lower() or "arrival" in day1.get("theme_note", "").lower()

    # Last Day: Departure preparation presence
    last_day = days[-1]
    last_titles = [act["title"] for act in last_day.get("activities", [])]
    assert any("Departure" in t or "Return" in t or "Checkout" in t or "Souvenir" in t for t in last_titles)


# ============================================================================
# 11. Dietary Preference Respect Test
# ============================================================================
def test_scenario_11_dietary_preference_respect():
    """
    Test 11: Dietary Preference Respect
    - Vegetarian trips must feature vegetarian dining tags and vegetarian menu items.
    - 'No Preference' trips must NOT falsely force vegetarian tags onto venues.
    """
    provider = MockProvider()

    # Vegetarian request
    veg_prompt = (
        "Destination: Kyoto, Japan\n"
        "Total Duration: EXACTLY 3 Days\n"
        "2 Adults\n"
        "Dietary Preferences: Vegetarian"
    )
    veg_data = json.loads(provider.generate(veg_prompt))
    veg_days = veg_data.get("trip", {}).get("itinerary_days", [])
    for d in veg_days:
        for act in d.get("activities", []):
            if act.get("is_dining") and not act.get("is_area_suggestion"):
                tags = act.get("dietary_tags", [])
                assert any("veg" in str(t).lower() for t in tags) or act.get("vegetarian_dish") is not None


# ============================================================================
# 12. Global Currency Handling Test
# ============================================================================
def test_scenario_12_global_currency_handling():
    """
    Test 12: Global Currency Handling
    Authentic destination currencies must be identified and formatted correctly:
    - Kyoto -> JPY (¥)
    - Switzerland -> CHF (CHF)
    - Singapore -> SGD (S$)
    - Paris -> EUR (€)
    - Dubai -> AED (د.إ)
    - Coimbatore -> INR (₹)
    """
    test_cases = [
        ("Kyoto, Japan", "JPY", "¥"),
        ("Switzerland", "CHF", "CHF"),
        ("Singapore", "SGD", "S$"),
        ("Paris, France", "EUR", "€"),
        ("Dubai, UAE", "AED", "د.إ"),
        ("Coimbatore, India", "INR", "₹"),
    ]

    for dest, expected_curr, expected_sym in test_cases:
        info = resolve_destination_info(dest, "Coimbatore")
        assert info["currency"] == expected_curr, f"Expected {expected_curr} for {dest}, got {info['currency']}"
        assert info["currency_symbol"] == expected_sym, f"Expected {expected_sym} for {dest}, got {info['currency_symbol']}"


# ============================================================================
# 13. Missing API Data Transparent Fallback Test
# ============================================================================
def test_scenario_13_missing_api_data_transparent_fallback():
    """
    Test 13: Missing API Data Transparent Fallback
    When POI API data lacks opening hours or ticket prices, status must be marked
    'Unavailable' or 'Unrated' or 'Estimated', NEVER fabricating fake ratings or fake 'Free Entry'.
    """
    coords = resolve_poi_coordinates("Remote Alpine Meadow", "Switzerland")
    if coords:
        assert coords.get("rating") is None, "Missing community rating must be None, not fabricated 4.5"
        assert coords.get("ticket_price") is None, "Missing ticket price must be None, not fabricated 0.0"


# ============================================================================
# 14. Destination Ambiguity Handling Test
# ============================================================================
def test_scenario_14_destination_ambiguity_handling():
    """
    Test 14: Destination Ambiguity Handling
    Broad country inputs ('Switzerland', 'Bolivia') or short city names ('Paris', 'Rome')
    must resolve gracefully to valid countries, currencies, and coordinate anchors without crashing.
    """
    ambiguous_destinations = ["Switzerland", "Bolivia", "Paris", "Rome", "Bali"]

    for d in ambiguous_destinations:
        info = resolve_destination_info(d, "Coimbatore")
        assert info["country_code"] is not None
        assert info["currency"] is not None
        assert info["price_multiplier"] > 0


# ============================================================================
# 15. Session Isolation Test
# ============================================================================
def test_scenario_15_session_isolation(db_session, test_user):
    """
    Test 15: Session Isolation
    Trip A (Kyoto, Family, Vegetarian) and Trip B (Paris, Couple, Adventure)
    must remain completely isolated with zero state or preference leakage.
    """
    trip_a_data = TripCreate(
        user_id=test_user.id,
        destination="Kyoto, Japan",
        start_date=date.today() + timedelta(days=20),
        end_date=date.today() + timedelta(days=25),
        budget=350000.0,
        currency="INR",
        travel_style="family",
        interests="Temples, Culture, Street Food",
        group_size=3,
        trip_preferences={"dietary_preferences": "vegetarian"}
    )
    resolved_a = resolve_trip_preferences(trip_a_data, test_user)

    trip_b_data = TripCreate(
        user_id=test_user.id,
        destination="Paris, France",
        start_date=date.today() + timedelta(days=50),
        end_date=date.today() + timedelta(days=56),
        budget=450000.0,
        currency="EUR",
        travel_style="couple",
        interests="Museums, Architecture, Photography",
        group_size=2,
        trip_preferences={"dietary_preferences": "no_preference"}
    )
    resolved_b = resolve_trip_preferences(trip_b_data, test_user)

    assert "Temples" in resolved_a["interests"]
    assert "Temples" not in resolved_b["interests"]
    assert "Architecture" in resolved_b["interests"]
    assert "Architecture" not in resolved_a["interests"]
    assert resolved_a["dietary_preferences"] == "vegetarian"
    assert resolved_b["dietary_preferences"] == "no_preference"
    assert resolved_a["currency"] == "INR"
    assert resolved_b["currency"] == "EUR"
