import pytest
import datetime
import json
from app.services.location.location_normalizer import (
    resolve_destination_info,
    COUNTRY_CODE_TO_CURRENCY,
    COUNTRY_CODE_TO_TIMEZONE,
    DESTINATION_PRICE_INDEX,
)
from app.services.route_optimizer import destination_has_rail, is_water_crossing, estimate_travel_transition
from app.services.weather.openmeteo_service import get_openmeteo_weather, get_seasonal_climate_standard
from app.services.poi_service import fetch_real_pois_for_destination, is_valid_destination_poi
from app.services.currency_service import CurrencyService
from app.services.budget_allocation_service import BudgetAllocationService, format_currency
from app.ai.providers.mock_provider import MockProvider
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator


# ==============================================================================
# SECTION 1: GLOBAL DESTINATION SUPPORT & DYNAMIC GEOCODING
# ==============================================================================
def test_global_destination_support_all_archetypes():
    """
    Verify dynamic resolution of city, ISO country code, currency, timezone,
    and market pricing multipliers for all 8 representative archetypes.
    """
    archetypes = [
        ("Tokyo", "JP", "JPY", "¥", "Asia/Tokyo", 1.1),
        ("Istanbul", "TR", "TRY", "₺", "Europe/Istanbul", 0.85),
        ("Bali", "ID", "IDR", "Rp", "Asia/Makassar", 0.50),
        ("Reykjavik", "IS", "ISK", "kr", "Atlantic/Reykjavik", 2.2),
        ("Paris", "FR", "EUR", "€", "Europe/Paris", 1.6),
        ("Singapore", "SG", "SGD", "S$", "Asia/Singapore", 2.0),
        ("Tromso", "NO", "NOK", "kr", "Europe/Oslo", 2.2),
        ("Cusco", "PE", "PEN", "S/", "America/Lima", 0.65),
    ]

    for city, exp_cc, exp_curr, exp_sym, exp_tz, exp_mult in archetypes:
        info = resolve_destination_info(city)
        assert info["country_code"] == exp_cc, f"{city} country_code mismatch"
        assert info["currency"] == exp_curr, f"{city} currency mismatch"
        assert info["currency_symbol"] == exp_sym, f"{city} currency_symbol mismatch"
        assert info["timezone"] == exp_tz, f"{city} timezone mismatch"
        assert info["price_multiplier"] == exp_mult, f"{city} price multiplier mismatch"
        assert info["latitude"] is not None and info["longitude"] is not None, f"{city} coordinates missing"
        assert "UTC" in info["utc_offset"], f"{city} UTC offset missing"


def test_origin_corridor_evaluation_domestic_vs_international():
    """
    Verify origin-destination corridor classification:
    - Domestic Japan (Tokyo -> Kyoto)
    - Domestic France (Paris -> Nice)
    - Domestic India (Coimbatore -> Delhi)
    - International Transcontinental (Coimbatore -> Tokyo)
    """
    # Domestic Japan
    jp_dom = resolve_destination_info("Kyoto", "Tokyo")
    assert jp_dom["is_domestic"] is True
    assert jp_dom["is_international"] is False
    assert jp_dom["is_long_haul"] is False

    # Domestic France
    fr_dom = resolve_destination_info("Nice", "Paris")
    assert fr_dom["is_domestic"] is True
    assert fr_dom["is_international"] is False

    # Domestic India
    in_dom = resolve_destination_info("Delhi", "Coimbatore")
    assert in_dom["is_domestic"] is True
    assert in_dom["is_india_domestic"] is True
    assert in_dom["currency"] == "INR"

    # International Long-haul
    intl_lh = resolve_destination_info("Tokyo", "Coimbatore")
    assert intl_lh["is_domestic"] is False
    assert intl_lh["is_international"] is True


# ==============================================================================
# SECTION 2: TRANSPORTATION INTELLIGENCE (RAIL VS NON-RAIL & WATER CROSSINGS)
# ==============================================================================
def test_modal_feasibility_rail_vs_non_rail():
    """
    Verify destinations without passenger rail (Reykjavik, Bali, Tromsø, Cusco, Queenstown)
    are strictly flagged as non-rail. Rail hubs (Tokyo, Paris, Singapore, Istanbul) support rail.
    """
    non_rail_targets = ["Reykjavik", "Bali", "Tromso", "Tromsø", "Cusco", "Queenstown"]
    rail_targets = ["Tokyo", "Paris", "Singapore", "Istanbul", "London", "Berlin"]

    for nr in non_rail_targets:
        assert destination_has_rail(nr) is False, f"{nr} should NOT have passenger rail"

    for r in rail_targets:
        assert destination_has_rail(r) is True, f"{r} should support passenger rail"


def test_maritime_water_crossing_detection():
    """
    Verify water crossing detection prevents impossible straight-line road transit.
    """
    # Bali mainland (Sanur) to Nusa Penida
    is_water, label = is_water_crossing(-8.67, 115.26, -8.72, 115.54, "Bali")
    assert is_water is True
    assert "Badung Strait" in label or "Boat" in label

    # Venice lagoon to outer island
    is_water_v, label_v = is_water_crossing(45.43, 12.33, 45.46, 12.36, "Venice")
    assert is_water_v is True
    assert "Vaporetto" in label_v or "Water Bus" in label_v


# ==============================================================================
# SECTION 3: UNIVERSAL BUDGET ALLOCATION & CURRENCY CONVERSIONS
# ==============================================================================
def test_canonical_budget_calculation_mathematical_consistency():
    """
    Test canonical budget allocation formula:
    remaining_budget = round(total_user_budget - total_estimated_trip_cost, 2)
    Category percentages sum to exactly 100.0%.
    Emergency reserve is protected and not double counted.
    """
    destinations = [
        ("Tokyo", "JPY", 600000.0),
        ("Paris", "EUR", 5000.0),
        ("Reykjavik", "ISK", 800000.0),
        ("Bali", "IDR", 30000000.0),
        ("Tromso", "NOK", 40000.0),
        ("Cusco", "PEN", 12000.0),
    ]

    for dest, curr, total_b in destinations:
        plan = BudgetAllocationService.calculate_plan(
            total_budget=total_b,
            currency=curr,
            trip_days=5,
            nights=4,
            adults=2,
            children=1,
            destination=dest,
            origin_city="Coimbatore",
            travel_style="mid_range"
        )
        tot_budget = plan["total_user_budget"]
        est_cost = plan["total_estimated_trip_cost"]
        rem = plan["remaining_budget"]

        # Exact formula validation
        expected_rem = round(tot_budget - est_cost, 2)
        assert rem == expected_rem, f"{dest} remaining_budget formula mismatch"

        # Percentage sum check
        pcts = [c["percentage"] for c in plan["categories"]]
        assert abs(sum(pcts) - 100.0) < 0.05, f"{dest} category percentages must sum to 100%"

        # Emergency reserve integrity (prevent double counting)
        emerg = plan["emergency_reserve"]
        assert emerg > 0, f"{dest} emergency reserve must be positive"
        assert plan["unallocated_balance"] == rem, f"{dest} unallocated balance must equal remaining budget without double-deducting emergency reserve"


def test_room_count_occupancy_standard():
    """
    Verify room count calculation:
    - 1 traveler -> 1 room
    - 2 adults + 1 child (family style) -> 1 family room
    - 4 adults -> 2 rooms
    """
    # 1 traveler
    p1 = BudgetAllocationService.calculate_plan(
        total_budget=200000, currency="INR", trip_days=3, nights=2, adults=1, children=0, destination="Tokyo"
    )
    assert p1["num_rooms"] == 1

    # 2 adults + 1 child family mode
    p2 = BudgetAllocationService.calculate_plan(
        total_budget=400000, currency="INR", trip_days=3, nights=2, adults=2, children=1, destination="Tokyo", travel_style="family"
    )
    assert p2["num_rooms"] == 1

    # 4 adults
    p3 = BudgetAllocationService.calculate_plan(
        total_budget=600000, currency="INR", trip_days=3, nights=2, adults=4, children=0, destination="Tokyo"
    )
    assert p3["num_rooms"] == 2


# ==============================================================================
# SECTION 4: WEATHER HORIZON BOUNDARY (14-DAY RULE)
# ==============================================================================
def test_weather_horizon_14_day_rule():
    """
    Verify weather service returns Seasonal Climate Standard for dates > 14 days in the future.
    """
    future_date = (datetime.date.today() + datetime.timedelta(days=45)).isoformat()
    reyk_weather = get_openmeteo_weather(64.1466, -21.9426, "Reykjavik", target_date=future_date)
    assert reyk_weather["weather_confidence"] == "Seasonal Climate Standard"
    assert reyk_weather["source"] == "Historical Regional Climate Benchmark"
    assert reyk_weather["temp_c"] is not None

    bali_weather = get_openmeteo_weather(-8.4095, 115.1889, "Bali", target_date=future_date)
    assert bali_weather["weather_confidence"] == "Seasonal Climate Standard"
    assert bali_weather["temp_c"] >= 20.0, "Bali tropical climate should be warm"


# ==============================================================================
# SECTION 5: POI DISCOVERY & TRANSPARENT DEGRADATION
# ==============================================================================
def test_universal_poi_retrieval_archetypes():
    """
    Verify verified POIs exist for Reykjavik, Tromso, Cusco, Paris, Tokyo, Bali, Singapore, Istanbul.
    All POIs must have verified coordinates and valid categories.
    """
    cities = ["Reykjavik", "Tromso", "Cusco", "Paris", "Tokyo", "Bali", "Singapore", "Istanbul"]
    for city in cities:
        pois = fetch_real_pois_for_destination(city)
        assert len(pois) >= 5, f"{city} must return at least 5 verified POIs"
        for p in pois:
            assert p.get("latitude") is not None and p.get("longitude") is not None, f"POI in {city} missing coords"
            assert is_valid_destination_poi(p, city), f"POI {p.get('name')} in {city} failed validity check"


# ==============================================================================
# SECTION 6: END-TO-END ITINERARY GENERATION & ZERO OVERLAPS
# ==============================================================================
def test_end_to_end_itinerary_generation_all_archetypes():
    """
    Generate and validate 3-day itineraries for all 8 archetype destinations:
    - Zero overlapping activities (start_{i+1} >= end_i + 20m)
    - Diurnal ordering strictly maintained
    - Dietary preference (Vegetarian) strictly enforced without meat or seafood
    - Non-rail destinations never receive Metro/Train suggestions
    """
    provider = MockProvider()
    destinations = ["Tokyo", "Istanbul", "Bali", "Reykjavik", "Paris", "Singapore", "Tromso", "Cusco"]

    s_date = datetime.date(2027, 3, 10)
    e_date = datetime.date(2027, 3, 12)

    for dest in destinations:
        prompt = (
            f"Destination: {dest}\n"
            f"Origin City: Coimbatore, India\n"
            f"Duration: 3 days\n"
            f"2 Adults, 1 Child\n"
            f"Travel Style: standard\n"
            f"Traveler dietary requirement: \"Vegetarian\""
        )
        raw_res = provider.generate(prompt)
        data = json.loads(raw_res)
        assert "trip" in data, f"{dest} missing 'trip' key"
        days = data["trip"]["itinerary_days"]
        assert len(days) == 3, f"{dest} expected 3 days, got {len(days)}"

        # Validate with FinalItineraryValidator
        is_valid, issues, cleaned_days = FinalItineraryValidator.validate_itinerary_payload(
            days_data=days,
            destination=dest,
            start_date=s_date,
            end_date=e_date,
            expected_days=3,
            currency="INR",
            dietary_preferences="Vegetarian",
            travelers_count=3,
            adults_count=2,
            children_count=1
        )

        assert is_valid, f"{dest} validation failed with issues: {issues}"
        assert len(cleaned_days) == 3

        # Validate non-rail transport mode check
        has_rail = destination_has_rail(dest)
        for day in cleaned_days:
            for act in day["activities"]:
                t_mode = str(act.get("transport_mode", "")).lower()
                if not has_rail:
                    assert not any(k in t_mode for k in ["metro", "subway", "bullet train", "mrt", "tram"]), \
                        f"{dest} is non-rail but has transport_mode '{t_mode}' in activity '{act['title']}'"


def test_sparse_destination_graceful_degradation():
    """
    Test itinerary generation for a remote destination with no curated POIs in database.
    Verifies that the system generates transparent self-guided exploration blocks
    (is_area_suggestion=True) with ZERO invented businesses and ZERO duplicates.
    """
    provider = MockProvider()
    remote_dest = "Remote Arctic Outpost, Norway"

    prompt = (
        f"Destination: {remote_dest}\n"
        f"Origin City: Coimbatore, India\n"
        f"Duration: 3 days\n"
        f"2 Adults\n"
        f"Travel Style: standard\n"
        f"Traveler dietary requirement: \"Vegetarian\""
    )
    raw_res = provider.generate(prompt)
    data = json.loads(raw_res)
    assert "trip" in data
    days = data["trip"]["itinerary_days"]
    assert len(days) == 3, "Expected 3 days generated"

    all_titles = []
    for day in days:
        for act in day["activities"]:
            title = act["title"]
            all_titles.append(title)
            if act.get("is_dining") and act.get("is_area_suggestion"):
                assert "Area Dining" in title
            elif act.get("activity_type") == "area_suggestion":
                assert act.get("is_area_suggestion") is True

    # Check zero duplicates across days
    assert len(all_titles) == len(set(all_titles)), f"Duplicate activity titles found: {all_titles}"
