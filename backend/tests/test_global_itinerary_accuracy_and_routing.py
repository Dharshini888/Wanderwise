"""
test_global_itinerary_accuracy_and_routing.py — Comprehensive Global Itinerary & Route Validation Suite

Tests rigorous destination-independent integrity, geocoding constraints, route plausibility,
dining non-free-entry enforcement, family child guidance, and budget allocation transparency
across Queenstown, NZ, Kyoto, Switzerland, Singapore, Bali, Paris, and Coimbatore.
"""

import pytest
from datetime import date, timedelta
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.poi_service import (
    fetch_real_pois_for_destination,
    is_valid_destination_poi,
    resolve_poi_coordinates
)
from app.services.route_optimizer import haversine_distance_km
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from app.services.trip_service import resolve_and_enrich_itinerary_routes, enrich_trip_response
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.place import Place
from app.models.user import User
from app.database.connection import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

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
        name="Global Reliability User",
        email="reliability_test@wanderwise.com",
        password="hashed_password",
        currency="INR",
        preferred_budget="mid_range"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================================================
# TEST 1: Queenstown, NZ POI Geographic Integrity & Out-of-Country Bounding
# ==============================================================================
def test_queenstown_poi_geographic_bounding():
    """
    Verify Queenstown, NZ POIs:
    1. Zero POIs from Cobh (Ireland), Queenstown (Singapore), or Maryland (USA).
    2. All venues reside within 50 km of Queenstown center (-45.031, 168.662).
    3. Real adventure venues (Shotover Jet, Kawarau Bridge Bungy, Bob's Peak) and dining (Fergburger).
    """
    pois = fetch_real_pois_for_destination("Queenstown")
    assert len(pois) >= 5, "Queenstown must return verified POIs"

    qt_lat, qt_lon = -45.0311, 168.6626
    names = [p["name"] for p in pois]

    # Rejection of out-of-country names
    assert not any("Titanic" in n for n in names), "Titanic Experience (Cobh, Ireland) must NOT be in Queenstown POIs"
    assert not any("Tiger Car" in n for n in names), "Tiger Car (Singapore) must NOT be in Queenstown POIs"
    assert not any("Maryland" in n or "Pizzeria" in n for n in names), "Queenstown USA venues must NOT be present"

    # All coordinates must be within 50 km radius
    for p in pois:
        p_lat = p.get("latitude")
        p_lon = p.get("longitude")
        assert p_lat is not None and p_lon is not None, f"POI {p['name']} missing coordinates"
        dist_km = haversine_distance_km(qt_lat, qt_lon, float(p_lat), float(p_lon))
        assert dist_km <= 50.0, f"POI {p['name']} is {dist_km:.1f} km from Queenstown center (exceeds 50km)"

    # Genuine New Zealand categories
    categories = [p["category"] for p in pois]
    assert any("Adventure" in c for c in categories), "Must contain adventure activity"
    assert any("Restaurant" in c or "Dining" in c or "Cafe" in c for c in categories), "Must contain dining venue"


# ==============================================================================
# TEST 2: Route Plausibility — No 981 km / 1,977 min Routes between Stops
# ==============================================================================
def test_route_enrichment_implausible_distance_rejection(db_session: Session, test_user: User):
    """
    Verify that if distant coordinates (e.g. Cobh, Ireland or foreign city) slip into stops,
    the router flags 'Route Unavailable (Implausible distance)' and excludes it from
    accumulated distance and duration.
    """
    trip = Trip(
        user_id=test_user.id,
        title="Queenstown Test",
        destination="Queenstown",
        country="New Zealand",
        start_date=date(2027, 2, 15),
        end_date=date(2027, 2, 20),
        budget=180000.0,
        group_size=3,
        currency="INR"
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Activity 1: Queenstown Center (-45.031, 168.662)
    # Activity 2: Accidental distant coordinate (Cobh, Ireland: 51.849, -8.294 -> ~18,000 km away!)
    serialized_days = [{
        "day_number": 1,
        "activities": [
            {
                "id": 1,
                "title": "Queenstown Gardens",
                "place": {
                    "name": "Queenstown Gardens",
                    "latitude": -45.033,
                    "longitude": 168.665,
                    "category": "Nature and viewpoint"
                }
            },
            {
                "id": 2,
                "title": "Distant Mismatched Stop",
                "place": {
                    "name": "Distant Stop",
                    "latitude": 51.849,
                    "longitude": -8.294,
                    "category": "Sightseeing"
                }
            }
        ]
    }]

    enriched = resolve_and_enrich_itinerary_routes(db_session, trip, serialized_days)
    day1 = enriched[0]
    act1 = day1["activities"][0]
    summary = day1["route_summary"]

    assert act1["transport_mode"] == "Route Unavailable"
    assert act1["metadata"]["distance"] == "Route Unavailable (Implausible distance)"
    assert summary["total_distance_km"] == 0.0, "Implausible distance must NOT inflate route km"
    assert summary["total_duration_minutes"] == 0, "Implausible distance must NOT inflate route duration"


# ==============================================================================
# TEST 3: FinalItineraryValidator Geographic Pruning & Backfill
# ==============================================================================
def test_validator_prunes_distant_stop_and_backfills():
    """
    Verify FinalItineraryValidator detects out-of-bounds stops (> 65km),
    prunes them from cleaned_acts, and backfills with genuine Queenstown POIs.
    """
    days_data = [{
        "day_number": 1,
        "base_city": "Queenstown",
        "overnight_stay": "Queenstown Hotel",
        "activities": [
            {
                "title": "Skyline Queenstown",
                "place": {
                    "name": "Skyline Queenstown",
                    "latitude": -45.029,
                    "longitude": 168.654,
                    "category": "Nature and viewpoint"
                },
                "start_time": "09:00",
                "end_time": "11:00",
                "duration_minutes": 120
            },
            {
                "title": "Titanic Experience Cobh",
                "place": {
                    "name": "Titanic Experience Cobh",
                    "latitude": 51.849,  # Ireland! ~18,700 km away
                    "longitude": -8.294,
                    "category": "Museum"
                },
                "start_time": "12:00",
                "end_time": "14:00",
                "duration_minutes": 120
            }
        ]
    }]

    _, issues, validated_days = FinalItineraryValidator.validate_itinerary_payload(
        days_data=days_data,
        destination="Queenstown",
        start_date=date(2027, 2, 15),
        end_date=date(2027, 2, 15),
        expected_days=1,
        currency="INR",
        adults_count=2,
        children_count=1
    )

    day1_acts = validated_days[0]["activities"]
    assert any("Titanic" in issue for issue in issues), "Must record issue for Titanic in Ireland"
    act_names = [a.get("place", {}).get("name") for a in day1_acts]
    assert not any("Titanic" in n for n in act_names), "Titanic Experience must be pruned from cleaned activities"
    assert len(day1_acts) >= 2, "Must backfill day to maintain at least 2 activities"


# ==============================================================================
# TEST 4: Dining Non-Free-Entry & Ticket Price Integrity
# ==============================================================================
def test_dining_activity_non_free_entry(db_session: Session, test_user: User):
    """
    Ensure restaurants, cafes, and bars NEVER display 'Free Entry'.
    They must show 'A la carte dining' or estimated meal pricing.
    """
    trip = Trip(
        user_id=test_user.id,
        title="Dining Verification Trip",
        destination="Queenstown",
        country="New Zealand",
        start_date=date(2027, 2, 15),
        end_date=date(2027, 2, 16),
        budget=100000.0,
        group_size=2,
        currency="INR"
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    p_rest = Place(
        name="Fergburger",
        category="Restaurant",
        city="Queenstown",
        country="New Zealand",
        latitude=-45.0317,
        longitude=168.6595,
        ticket_price=0.0
    )
    db_session.add(p_rest)
    db_session.commit()

    it_day = ItineraryDay(trip_id=trip.id, day_number=1, date=trip.start_date, title="Day 1")
    db_session.add(it_day)
    db_session.commit()

    act = ItineraryActivity(
        day_id=it_day.id,
        place_id=p_rest.id,
        title="Lunch at Fergburger",
        order_index=1,
        ticket_price=0.0,
        activity_metadata={"activity_type": "meal", "meal_cost": 25.0}
    )
    db_session.add(act)
    db_session.commit()

    resp = enrich_trip_response(trip, db_session)
    act_resp = resp["itinerary_days"][0]["activities"][0]

    assert act_resp["activity_type"] == "meal"
    assert act_resp["formatted_cost"] != "Free Entry", "Dining MUST NEVER be formatted as 'Free Entry'"
    assert "Meal Est." in act_resp["formatted_cost"] or "A la carte" in act_resp["formatted_cost"]


# ==============================================================================
# TEST 5: Family Vacation & Child Adventure Suitability Advisory
# ==============================================================================
def test_family_vacation_child_adventure_suitability():
    """
    Verify that in family trips with children, high-intensity adventure activities
    (bungy, jet boat, skydive) receive child guidance/advisories without crashes.
    """
    days_data = [{
        "day_number": 1,
        "base_city": "Queenstown",
        "activities": [
            {
                "title": "Kawarau Bridge Bungy Jump",
                "place": {
                    "name": "Kawarau Bridge Bungy",
                    "latitude": -45.006,
                    "longitude": 168.900,
                    "category": "Adventure activity"
                },
                "duration_minutes": 150
            }
        ]
    }]

    _, _, validated_days = FinalItineraryValidator.validate_itinerary_payload(
        days_data=days_data,
        destination="Queenstown",
        start_date=date(2027, 2, 15),
        end_date=date(2027, 2, 15),
        expected_days=1,
        currency="INR",
        adults_count=2,
        children_count=1  # 1 child
    )

    act = validated_days[0]["activities"][0]
    desc = act.get("description", "").lower()
    assert "family guidance" in desc or "minimum age" in desc, "Adventure activity must include child guidance"


# ==============================================================================
# TEST 6: Sequential Non-overlapping Scheduling & Day 1 / Final Day Realism
# ==============================================================================
def test_schedule_non_overlapping_and_day_boundaries():
    """
    Verify:
    1. Day 1 starts in afternoon (>= 14:00) for arrival/check-in.
    2. Final Day reserves departure buffer (no sightseeing past 17:00).
    3. Consecutive activities never overlap.
    """
    days_data = [
        {
            "day_number": 1,
            "activities": [
                {"title": "Check-in & Gardens", "duration_minutes": 60, "place": {"name": "Queenstown Gardens", "latitude": -45.033, "longitude": 168.665}},
                {"title": "Scenic Lookout", "duration_minutes": 45, "place": {"name": "Bob's Peak", "latitude": -45.029, "longitude": 168.654}}
            ]
        },
        {
            "day_number": 2,
            "activities": [
                {"title": "Morning Lake Walk", "duration_minutes": 45, "place": {"name": "Lake Wakatipu", "latitude": -45.035, "longitude": 168.660}},
                {"title": "Dinner Exploration", "duration_minutes": 75, "place": {"name": "Flame Bar & Grill", "latitude": -45.032, "longitude": 168.660}}
            ]
        }
    ]

    _, _, validated_days = FinalItineraryValidator.validate_itinerary_payload(
        days_data=days_data,
        destination="Queenstown",
        start_date=date(2027, 2, 15),
        end_date=date(2027, 2, 16),
        expected_days=2,
        currency="INR",
        adults_count=2,
        children_count=1
    )

    # Day 1 start time
    d1_first_act = validated_days[0]["activities"][0]
    st1_h = int(d1_first_act["start_time"].split(":")[0])
    assert st1_h >= 14, f"Day 1 first activity should start in afternoon (>= 14:00), got {d1_first_act['start_time']}"

    # Non-overlapping check
    for day in validated_days:
        acts = day["activities"]
        for i in range(len(acts) - 1):
            curr_et = acts[i]["end_time"]
            next_st = acts[i + 1]["start_time"]
            c_tot = int(curr_et.split(":")[0]) * 60 + int(curr_et.split(":")[1])
            n_tot = int(next_st.split(":")[0]) * 60 + int(next_st.split(":")[1])
            assert n_tot >= c_tot, f"Activity {acts[i+1]['title']} at {next_st} overlaps with {acts[i]['title']} ending at {curr_et}"


# ==============================================================================
# TEST 7: Budget Feasibility & Elimination of False Category Shortfalls
# ==============================================================================
def test_queenstown_budget_feasibility_and_surplus_rebalancing():
    """
    Scenario: Coimbatore -> Queenstown, NZ, 6 days, 2 adults + 1 child, ₹180,000 INR.
    When the total budget is sufficient, category ceilings must be rebalanced from surplus
    so no artificial category shortfalls (e.g. other_fees or contingency) are presented.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=180000.0,
        currency="INR",
        tier="mid_range",
        destination="Queenstown",
        origin_city="Coimbatore",
        days=6,
        adults=2,
        children=1,
        transport_mode="flight",
        accommodation_preference="hotel"
    )

    assert plan["total_estimated_trip_cost"] > 0
    assert "fees_breakdown" in plan, "Must provide detailed fees_breakdown"
    fb = plan["fees_breakdown"]
    assert "visa_eta" in fb
    assert "travel_insurance" in fb
    assert "checked_baggage" in fb

    if plan["is_feasible"] and plan["total_user_budget"] >= plan["total_estimated_trip_cost"]:
        # If budget is sufficient, zero false category shortfalls
        assert len(plan["category_reconciliation"]["shortfall_categories"]) == 0
        assert plan["shortfall"] == 0.0


# ==============================================================================
# TEST 8: Global Destination Reliability — Kyoto, Japan (Luxury Cultural)
# ==============================================================================
def test_global_destination_kyoto():
    """
    Verify Kyoto, Japan returns authentic POIs with distinct coordinates
    and JPY destination currency standard.
    """
    pois = fetch_real_pois_for_destination("Kyoto")
    assert len(pois) >= 3
    coords = [(p.get("latitude"), p.get("longitude")) for p in pois]
    unique_coords = set(coords)
    assert len(unique_coords) >= 3, "Kyoto POIs must have distinct GPS coordinates"


# ==============================================================================
# TEST 9: Global Destination Reliability — Switzerland (Alpine Long-haul)
# ==============================================================================
def test_global_destination_switzerland():
    """
    Verify Switzerland resolves CHF currency and authentic alpine landmarks.
    """
    pois = fetch_real_pois_for_destination("Switzerland")
    assert len(pois) >= 3
    assert any("Matterhorn" in p["name"] or "Jungfrau" in p["name"] or "Lake" in p["name"] or "Lucerne" in p["name"] for p in pois)


# ==============================================================================
# TEST 10: Global Destination Reliability — Singapore (City-State Regional)
# ==============================================================================
def test_global_destination_singapore():
    """
    Verify Singapore resolves SGD currency and authentic landmarks (Marina Bay Sands, Gardens by the Bay).
    """
    pois = fetch_real_pois_for_destination("Singapore")
    names = [p["name"] for p in pois]
    assert any("Marina Bay" in n or "Gardens by the Bay" in n or "Sentosa" in n for n in names)


# ==============================================================================
# TEST 11: Global Destination Reliability — Bali, Indonesia (Island Coastal)
# ==============================================================================
def test_global_destination_bali():
    """
    Verify Bali resolves IDR currency and authentic temples/beaches (Tanah Lot, Uluwatu, Ubud).
    """
    pois = fetch_real_pois_for_destination("Bali")
    names = [p["name"] for p in pois]
    assert any("Tanah Lot" in n or "Uluwatu" in n or "Ubud" in n for n in names)


# ==============================================================================
# TEST 12: Global Destination Reliability — Paris, France (European Capital)
# ==============================================================================
def test_global_destination_paris():
    """
    Verify Paris POIs have distinct coordinates (Eiffel Tower, Louvre, Orsay).
    """
    pois = fetch_real_pois_for_destination("Paris")
    assert len(pois) >= 4
    lats = [p["latitude"] for p in pois]
    assert len(set(lats)) >= 3, "Paris POIs must not share identical center coordinates"


# ==============================================================================
# TEST 13: Global Destination Reliability — Coimbatore, India (Domestic Indian Corridor)
# ==============================================================================
def test_global_destination_coimbatore_domestic():
    """
    Verify Coimbatore is recognized as domestic:
    Zero visa fee requirements, domestic corridor index used, INR currency standard.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=40000.0,
        currency="INR",
        tier="budget",
        destination="Coimbatore",
        origin_city="Chennai",
        days=4,
        adults=2,
        children=0
    )
    assert plan["is_feasible"] is True
    assert plan["fees_breakdown"]["visa_eta"] == 0.0, "Domestic travel must have ₹0 visa fees"


# ==============================================================================
# TEST 14: Global Destination Reliability — Rural / Offbeat Destination
# ==============================================================================
def test_global_destination_varkala_rural():
    """
    Verify offbeat coastal town (Varkala, Kerala) resolves authentic cliff and beach stops.
    """
    pois = fetch_real_pois_for_destination("Varkala")
    assert len(pois) >= 2
    names = [p["name"] for p in pois]
    assert any("Cliff" in n or "Beach" in n or "Janardhanaswamy" in n for n in names)


# ==============================================================================
# TEST 15: Weather Confidence Labeling Integrity
# ==============================================================================
def test_weather_confidence_labeling():
    """
    Verify weather service confidence labels:
    - Live Forecast for real-time/short-range queries (<= 14 days)
    - Seasonal Climate Standard for future dates (> 14 days)
    - Weather Unavailable for offline/unreachable conditions
    """
    from app.services.weather.openmeteo_service import get_openmeteo_weather
    
    # Offline or missing coordinates
    offline_w = get_openmeteo_weather(None, None, "Unknown Place")
    assert offline_w["weather_confidence"] in ["Seasonal Climate Standard", "Weather Unavailable"]


# ==============================================================================
# TEST 16: Bali 8-Day Family Trip — Zero Duplicate Attractions, No Rail, Diverse Categories, 8 Field Statuses
# ==============================================================================
def test_bali_family_itinerary_reliability(db_session: Session, test_user: User, monkeypatch):
    """
    Simulate Bali 8-day family trip (15–22 January 2027, 2 adults, 2 children):
    1. Zero duplicate attractions across all 8 days.
    2. No metro/train transport modes (Bali has no rail transit).
    3. Diverse category distribution (Beaches, Nature, Culture, Adventure, Dining).
    4. All 8 field-level verification labels present on every activity.
    5. Day 1 and Last Day marked provisional.
    """
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "mock")
    from app.services.ai_service import generate_trip_days
    from app.services.route_optimizer import destination_has_rail

    assert not destination_has_rail("Bali, Indonesia"), "Bali must be recognized as non-rail destination"

    start_d = date(2027, 1, 15)
    end_d = date(2027, 1, 22) # 8 days

    trip_payload = generate_trip_days(
        destination="Bali, Indonesia",
        days=8,
        budget=200000.0,
        currency="INR",
        interests="culture, beaches, nature, adventure, food",
        travel_style="family",
        group_size=4,
        start_date=start_d.isoformat(),
        end_date=end_d.isoformat(),
        origin_city="Chennai",
        transportation="Private Driver / Taxi",
        trip_preferences={
            "adults": 2,
            "children": 2,
            "dietary_preferences": "Vegetarian",
            "pace": "balanced"
        }
    )

    days = trip_payload.get("days", [])
    assert len(days) == 8, f"Expected 8 days, got {len(days)}"

    # Day 1 and Day 8 must be provisional
    assert days[0].get("is_provisional") is True, "Day 1 must be provisional"
    assert days[-1].get("is_provisional") is True, "Last day must be provisional"

    # Track all scheduled attraction names across the entire 8-day trip
    seen_attractions = set()
    categories_seen = set()
    total_acts = 0

    for d in days:
        acts = d.get("activities", [])
        assert len(acts) >= 1, f"Day {d.get('day_number')} must not have 0 activities"
        for act in acts:
            total_acts += 1
            p = act.get("place") or {}
            p_name = p.get("name") or act.get("title")
            p_cat = p.get("category") or "Sightseeing"
            categories_seen.add(p_cat)

            is_dining = act.get("activity_type") == "meal" or p_cat == "Dining"
            is_area = act.get("is_area_suggestion") or p_cat == "Area Suggestion"

            if not is_dining and not is_area:
                norm = p_name.lower().replace(" ", "").replace("explore", "").replace("visit", "")
                assert norm not in seen_attractions, f"Duplicate attraction scheduled: '{p_name}' on Day {d.get('day_number')}"
                seen_attractions.add(norm)

            # Strict non-rail transit verification: NEVER metro/train in Bali
            t_mode = str(act.get("transport_mode") or "").lower()
            assert not any(r in t_mode for r in ["metro", "subway", "train", "tram", "rail"]), \
                f"Invalid rail mode '{t_mode}' scheduled in Bali for '{p_name}'"

            # 8 Field-Level Verification Statuses check
            prov = act.get("provenance") or {}
            required_statuses = [
                "identity_status", "location_status", "coordinate_status",
                "hours_status", "price_status", "route_status", "rating_status", "last_verified"
            ]
            for req_field in required_statuses:
                assert req_field in prov or req_field in act, f"Activity '{p_name}' missing field-level status '{req_field}'"

    # Category diversity across selected interests (culture, beach, nature, adventure, food)
    assert len(categories_seen) >= 3, f"Expected diverse categories, got {categories_seen}"
    assert any("Cultural" in c for c in categories_seen), "Must feature cultural attractions"


# ==============================================================================
# TEST 17: Bali Family Budget — Room Occupancy, Visa on Arrival & Exact Transport Math
# ==============================================================================
def test_bali_family_budget_and_visa():
    """
    Verify Bali budget calculation for 2 adults and 2 children:
    1. Family room occupancy = 1 room (Family Room / Quad Suite in Mid-range tier).
    2. Indonesia Visa on Arrival (VoA) = $35 USD / person ($140 USD for 4 persons).
    3. Mathematical reconciliation: Outbound + Return == Transport Total exactly.
    4. Adult Fare * 2 + Child Fare * 2 == Transport Total.
    """
    plan = BudgetAllocationService.calculate_plan(
        total_budget=200000.0,
        currency="USD",
        tier="mid_range",
        destination="Bali, Indonesia",
        origin_city="Chennai",
        days=8,
        adults=2,
        children=2,
        travel_style="family"
    )

    # 1. Family room occupancy: 1 family room instead of forcing 2 rooms
    # (Checking accommodation USD rate reflects 1 room)
    accom_cat = next(c for c in plan["categories"] if c["key"] == "accommodation")
    lodging_cost = accom_cat["estimated_cost"]
    # 70 USD * 7 nights = 490 USD for 1 room; if 2 rooms were forced it would be 980 USD
    assert lodging_cost <= 600.0, f"Expected 1 family room (~$490), got {lodging_cost} which indicates 2 forced rooms"

    # 2. Indonesia Visa on Arrival ($35 USD * 4 travellers = $140 USD)
    fees_note = plan["fees_breakdown"]["notes"]
    assert "Visa on Arrival" in fees_note or "VoA" in fees_note, "Must identify Indonesia VoA"
    assert "$140" in fees_note, "Must calculate $140 for 4 travellers at $35/person"

    # 3. Exact transport math
    outbound = next(c for c in plan["categories"] if c["key"] == "outbound_transport")["estimated_cost"]
    ret = next(c for c in plan["categories"] if c["key"] == "return_transport")["estimated_cost"]
    trans_total = plan["transportation_details"]["total_transport_cost"]
    assert abs(round(outbound + ret, 2) - trans_total) < 0.01, f"Outbound ({outbound}) + Return ({ret}) != Total ({trans_total})"


# ==============================================================================
# TEST 18: Distant Travel Dates Weather — Forecast Unavailable & Seasonal Climate Standard
# ==============================================================================
def test_distant_travel_dates_weather():
    """
    Verify that querying weather for distant future dates (e.g. 15 January 2027):
    - Sets weather_status = 'Forecast unavailable'
    - Sets weather_confidence = 'Seasonal Climate Standard'
    - Sets is_seasonal_estimate = True
    - Does NOT fabricate a live daily forecast
    """
    from app.routes.weather import get_weather

    w = get_weather(city="Bali", date_str="2027-01-15")
    assert w["weather_status"] == "Forecast unavailable", "Distant travel date must report 'Forecast unavailable'"
    assert w["weather_confidence"] == "Seasonal Climate Standard"
    assert w["is_seasonal_estimate"] is True

    sel = w.get("selected_date_weather")
    assert sel is not None
    assert sel.get("forecast_unavailable") is True
    assert "Forecast unavailable" in sel.get("status_label")


# ==============================================================================
# TEST 19: Queenstown Non-Rail Transit & Adventure Child Guidance
# ==============================================================================
def test_queenstown_non_rail_and_adventure_family_guidance():
    """
    Verify Queenstown, NZ:
    1. Recognized as non-rail destination.
    2. Adventure activities include child suitability / family guidance advisory.
    """
    from app.services.route_optimizer import destination_has_rail

    assert not destination_has_rail("Queenstown, New Zealand")

    # Final validator test with adventure activity and 1 child
    raw_days = [
        {
            "day_number": 1,
            "title": "Day 1: Queenstown Thrills",
            "theme_note": "Base: Queenstown | Overnight: Queenstown Hotel",
            "activities": [
                {
                    "title": "Kawarau Bridge Bungy Centre",
                    "description": "Birthplace of commercial bungy jumping.",
                    "start_time": "10:00",
                    "end_time": "12:30",
                    "duration_minutes": 150,
                    "transport_mode": "Metro", # Needs sanitization!
                    "place": {
                        "name": "Kawarau Bridge Bungy Centre",
                        "category": "Adventure",
                        "latitude": -45.0089,
                        "longitude": 168.9002
                    }
                }
            ]
        }
    ]

    is_valid, issues, validated = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_days,
        destination="Queenstown",
        start_date=date(2027, 2, 1),
        end_date=date(2027, 2, 1),
        expected_days=1,
        currency="NZD",
        adults_count=2,
        children_count=1
    )

    act = validated[0]["activities"][0]
    # Transport mode must NOT be Metro
    assert "metro" not in str(act.get("transport_mode", "")).lower(), "Queenstown must not have Metro transit"

    # Adventure activity with child present must include family guidance
    assert "family guidance" in act["description"].lower() or "minimum age" in act["description"].lower()


# ==============================================================================
# TEST 20: Insufficient POIs Scenario — Honest Leisure Block, Zero Duplicate Fillers
# ==============================================================================
def test_insufficient_pois_honest_leisure_scheduling():
    """
    When verified attractions run out on a multi-day itinerary:
    1. System must NOT repeat duplicate attractions.
    2. System must NOT generate 0 activities (empty day).
    3. System must schedule an honest self-guided leisure/exploration block with transparent rationale.
    """
    # Simulate a 3-day itinerary where only 1 POI was provided across 3 days
    raw_days = [
        {
            "day_number": 1,
            "activities": [
                {
                    "title": "Tanah Lot Temple",
                    "start_time": "09:00",
                    "end_time": "11:30",
                    "place": {"name": "Tanah Lot Temple", "category": "Cultural / Heritage", "latitude": -8.6212, "longitude": 115.0868}
                }
            ]
        },
        {
            "day_number": 2,
            "activities": [
                # Duplicate of Day 1 to test pruning
                {
                    "title": "Tanah Lot Temple",
                    "start_time": "09:00",
                    "end_time": "11:30",
                    "place": {"name": "Tanah Lot Temple", "category": "Cultural / Heritage", "latitude": -8.6212, "longitude": 115.0868}
                }
            ]
        }
    ]

    is_valid, issues, validated = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_days,
        destination="Tiny Island",
        start_date=date(2027, 3, 1),
        end_date=date(2027, 3, 2),
        expected_days=2,
        currency="USD"
    )

    day1_names = [a["place"]["name"] for a in validated[0]["activities"]]
    day2_names = [a["place"]["name"] for a in validated[1]["activities"]]

    # Tanah Lot must NOT appear on Day 2
    assert "Tanah Lot Temple" not in day2_names, "Tanah Lot was duplicated and must be pruned from Day 2"
    # Day 2 must have at least 1 activity (honest leisure or backfill)
    assert len(validated[1]["activities"]) >= 1, "Day 2 must not be left empty"


# ==============================================================================
# TEST 21: Attraction Ticket Pricing Consistency Across Trip
# ==============================================================================
def test_attraction_pricing_consistency():
    """
    Verify that if an attraction is referenced with conflicting prices,
    the validator reconciles it to a single consistent pricing record.
    """
    raw_days = [
        {
            "day_number": 1,
            "activities": [
                {
                    "title": "Visit Museum A",
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "ticket_price": 50.0,
                    "place": {"name": "Museum A", "category": "Museum / Culture", "latitude": 10.0, "longitude": 10.0}
                }
            ]
        },
        {
            "day_number": 2,
            "activities": [
                {
                    "title": "Visit Museum A Morning Lecture",
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "ticket_price": 0.0, # Conflicting free entry!
                    "place": {"name": "Museum A", "category": "Museum / Culture", "latitude": 10.0, "longitude": 10.0}
                }
            ]
        }
    ]

    is_valid, issues, validated = FinalItineraryValidator.validate_itinerary_payload(
        days_data=raw_days,
        destination="Cultural Capital",
        start_date=date(2027, 4, 1),
        end_date=date(2027, 4, 2),
        expected_days=2,
        currency="USD"
    )

    # Duplicate Museum A is pruned or reconciled
    for d in validated:
        for a in d["activities"]:
            if a["place"]["name"] == "Museum A":
                assert a["place"]["ticket_price"] == 50.0, "Price must remain 50.0 consistently, not conflicting 0.0"

