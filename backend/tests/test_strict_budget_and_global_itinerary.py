import pytest
from datetime import date, timedelta
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.poi_service import fetch_real_pois_for_destination, resolve_poi_coordinates
from app.services.location.location_normalizer import resolve_destination_info
from app.schemas.trip_schemas import TripCreate
from app.routes.trips import resolve_trip_preferences, create_new_trip
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import app.models
from app.database.connection import Base
from app.models.user import User

# Setup in-memory SQLite database
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
        name="Budget Test User",
        email="test_strict_budget@wanderwise.com",
        password="hashed_pw_test",
        currency="INR",
        preferred_budget="mid_range"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_scenario_1_strict_budget_feasibility_switzerland():
    """
    TEST 1: Strict Budget Feasibility Blocking
    Scenario: Coimbatore -> Switzerland, 8 Days, 2 Adults + 2 Children, Budget: ₹100,000 INR.
    Must calculate minimum realistic budget (~₹8,80,000), flag is_feasible=False,
    and have a shortfall of ~₹7,80,000 with affordable alternatives.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=100000.0,
        currency="INR",
        tier="mid_range",
        destination="Switzerland",
        origin_city="Coimbatore",
        days=8,
        adults=2,
        children=2,
        transport_mode="flight",
        accommodation_preference="hotel"
    )

    assert plan["is_feasible"] is False, "₹100,000 for 4 people to Switzerland must NOT be feasible"
    assert plan["shortfall"] > 500000.0, f"Shortfall should be large (got {plan['shortfall']})"
    assert plan["total_estimated_trip_cost"] > 700000.0
    assert len(plan["affordable_alternatives"]) >= 2
    alt_names = [a["name"] for a in plan["affordable_alternatives"]]
    assert any("Manali" in n or "Solang" in n for n in alt_names)
    assert any("Nepal" in n or "Kathmandu" in n for n in alt_names)


def test_scenario_2_feasible_switzerland_with_real_attractions():
    """
    TEST 2: Feasible Switzerland Trip & Global Real POI Support
    Scenario: Coimbatore -> Switzerland, ₹1,000,000 INR budget.
    Must be feasible, and POI service must return genuine Swiss attractions with coordinates.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=1000000.0,
        currency="INR",
        tier="mid_range",
        destination="Switzerland",
        origin_city="Coimbatore",
        days=8,
        adults=2,
        children=2,
        transport_mode="flight",
        accommodation_preference="hotel"
    )

    assert plan["is_feasible"] is True
    assert plan["remaining_budget"] > 0
    assert plan["shortfall"] == 0.0

    # Test POI retrieval for Switzerland
    swiss_pois = fetch_real_pois_for_destination("Switzerland")
    assert len(swiss_pois) >= 10, f"Expected at least 10 authentic Swiss POIs, got {len(swiss_pois)}"

    poi_names = [p["name"] for p in swiss_pois]
    assert any("Grossmünster" in n or "Lake Zurich" in n for n in poi_names)
    assert any("Titlis" in n for n in poi_names)
    assert any("Jungfraujoch" in n for n in poi_names)

    # Verify coordinates exist
    titlis = next((p for p in swiss_pois if "Titlis" in p["name"]), None)
    assert titlis is not None
    assert titlis["latitude"] is not None and titlis["longitude"] is not None
    assert titlis["ticket_price"] > 0, "Mount Titlis should have admission fee"


def test_scenario_3_dynamic_calculation_singapore():
    """
    TEST 3: Dynamic Calculation for Singapore
    Scenario: Coimbatore -> Singapore, 6 Days, 2 Adults + 1 Child, ₹200,000 INR budget.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=200000.0,
        currency="INR",
        tier="mid_range",
        destination="Singapore",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=1,
        transport_mode="flight",
        accommodation_preference="hotel"
    )

    assert plan["total_estimated_trip_cost"] > 100000.0
    assert "transportation_details" in plan
    trans = plan["transportation_details"]
    assert trans["adult_fare_roundtrip"] > 0
    assert trans["child_fare_roundtrip"] > 0
    # Group transport should equal (2 * adult_fare) + (1 * child_fare)
    expected_trans = round((2 * trans["adult_fare_roundtrip"]) + (1 * trans["child_fare_roundtrip"]), 2)
    assert abs(trans["total_transport_cost"] - expected_trans) <= 1.0


def test_scenario_4_interest_tag_purity(test_user):
    """
    TEST 4: Interest Tag Purity
    When user specifies only "Nature, Photography, Culture", ensure resolve_trip_preferences
    preserves ONLY those three tags, without injecting "Solo", "Food & Dining", or "Sightseeing".
    """
    trip_data = TripCreate(
        user_id=test_user.id,
        destination="Switzerland",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=37),
        budget=1000000.0,
        currency="INR",
        travel_style="family",
        interests="Nature, Photography, Culture",
        group_size=4
    )

    resolved = resolve_trip_preferences(trip_data, test_user)
    assert resolved["interests"] == "Nature, Photography, Culture"
    tags = [t.strip() for t in resolved["interests"].split(",")]
    assert set(tags) == {"Nature", "Photography", "Culture"}
    assert "Solo" not in tags
    assert "Food & Dining" not in tags
    assert "Luxury Dining" not in tags


def test_scenario_5_adults_vs_children_recalculation():
    """
    TEST 5: Person-Based Traveler Count Recalculation
    Compare 2 Adults vs 2 Adults + 2 Children:
    - 2 Adults -> 1 room
    - 2 Adults + 2 Children (4 travelers) -> 2 rooms
    - Total transport increases due to child fares
    - Total food increases due to child meal rates
    """
    plan_2 = BudgetAllocationService.calculate_plan(
        total_budget=500000.0,
        currency="INR",
        tier="mid_range",
        destination="Singapore",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=0
    )

    plan_4 = BudgetAllocationService.calculate_plan(
        total_budget=500000.0,
        currency="INR",
        tier="mid_range",
        destination="Singapore",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=2
    )

    assert plan_2["num_rooms"] == 1
    assert plan_4["num_rooms"] == 2
    assert plan_4["accommodation_estimate"] > plan_2["accommodation_estimate"]
    assert plan_4["transportation_details"]["total_transport_cost"] > plan_2["transportation_details"]["total_transport_cost"]
    assert plan_4["food_estimate"] > plan_2["food_estimate"]
    assert plan_4["activities_estimate"] > plan_2["activities_estimate"]


def test_scenario_6_server_side_budget_block(db_session, test_user):
    """
    TEST 6: Server-Side Strict Budget Feasibility Blocking
    Calling create_new_trip with insufficient budget (₹100,000 for 8 days in Switzerland)
    must raise HTTPException with status 422 and detail error BUDGET_INSUFFICIENT.
    """
    trip_data = TripCreate(
        user_id=test_user.id,
        destination="Switzerland",
        start_date=date.today() + timedelta(days=60),
        end_date=date.today() + timedelta(days=67),
        budget=100000.0,
        currency="INR",
        travel_style="family",
        group_size=4,
        trip_preferences={
            "adults": 2,
            "children": 2,
            "origin_city": "Coimbatore",
            "budget_type": "mid_range"
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        create_new_trip(data=trip_data, db=db_session, current_user=test_user)

    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "BUDGET_INSUFFICIENT"
    assert detail.get("is_feasible") is False
    assert detail.get("shortfall") > 500000.0
    assert len(detail.get("affordable_alternatives", [])) >= 2


def test_scenario_7_transparent_benchmark_disclosures():
    """
    TEST 7: Accurate Data Provenance & Benchmark Disclosures
    Verify that transportation pricing basis is disclosed as market benchmark,
    not fake live reservations or static constant values.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=500000.0,
        currency="INR",
        tier="mid_range",
        destination="Switzerland",
        origin_city="Coimbatore",
        days=8,
        adults=2,
        children=2
    )

    trans = plan["transportation_details"]
    assert trans["pricing_type"] == "Market Benchmark"
    assert trans["is_market_benchmark"] is True
    assert trans["is_live_quote"] is False
    assert "IATA" in trans["source"] or "Benchmark" in trans["source"]
    assert plan["cost_provenance"]["accommodation"]["status"] == "Sourced estimate"
    assert plan["cost_provenance"]["food"]["status"] == "Sourced estimate"
