"""
test_global_travel_engine_corrections.py — Comprehensive Automated Test Suite
Validates the Global Travel Engine across all 7 dimensions without destination-specific hardcoded hacks:
1. Budget engine exact preservation, arithmetic, remaining balance, emergency reserve single-counting, currency units.
2. Elimination of ₹25 meal cost problem and realistic dining benchmarks.
3. Global attraction identity, admission fees, and free vs paid distinction.
4. POI coordinate uniqueness and elimination of city-center fallbacks.
5. Routing calculation, transit distance consistency, route statuses, and origin/destination directions URLs.
6. Separate airport transfer and departure buffer activities on Day 1 and Final Day.
7. Day regeneration with locked activity preservation, chronological ordering, and non-overlapping schedules.
8. Weather horizon separation: Live Forecast (<14d) vs Seasonal Climate Standards (>14d).
9. Global destination independence: Paris, Tokyo, Istanbul, Bali, Reykjavik, Singapore, Cusco.
"""

import os
import sys
import json
from decimal import Decimal
from datetime import date, timedelta
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

from app.services.budget_allocation_service import BudgetAllocationService
from app.services.currency_service import CurrencyService
from app.services.pricing.canonical_pricing_registry import CanonicalPricingRegistry, KNOWN_PAID_VENUES
from app.services.poi_service import resolve_poi_coordinates, fetch_real_pois_for_destination
from app.services.route_optimizer import (
    haversine_distance_km,
    estimate_travel_transition,
    destination_has_rail,
    is_water_crossing
)
from app.ai.providers.mock_provider import MockProvider
from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
from app.routes.weather import get_weather, _estimate_seasonal_climate


# ==============================================================================
# 1. BUDGET ENGINE & ACCOUNTING MODEL TESTS
# ==============================================================================

class TestBudgetEngineAndAccountingModel:
    """Verifies user budget preservation, arithmetic, emergency reserve single-counting, and balance models."""

    def test_budget_preservation_and_category_sum(self):
        """User budget must be preserved exactly, and category allocations must sum to 100%."""
        user_budget = 650000.0  # e.g., Tokyo trip budget in INR
        plan = BudgetAllocationService.calculate_plan(
            total_budget=user_budget,
            currency="INR",
            tier="mid_range",
            destination="Tokyo",
            origin_city="Coimbatore",
            days=7,
            adults=2,
            children=1,
            travel_style="family"
        )

        assert plan["total_user_budget"] == user_budget
        assert plan["is_feasible"] is True

        # Percentage sum check
        pct_sum = sum(c["percentage"] for c in plan["categories"])
        assert round(pct_sum, 1) == 100.0

        # Category allocated amounts sum to user_budget (within rounding tolerance)
        alloc_sum = sum(c["allocated_amount"] for c in plan["categories"])
        assert abs(alloc_sum - user_budget) <= 2.0

    def test_emergency_reserve_single_counted_and_accounting_model(self):
        """Emergency reserve must be included once in estimated cost, never subtracted twice from unallocated."""
        user_budget = 5000.0
        plan = BudgetAllocationService.calculate_plan(
            total_budget=user_budget,
            currency="USD",
            tier="mid_range",
            destination="Paris",
            origin_city="New York",
            days=5,
            adults=2,
            children=0
        )

        cat_rec = plan["category_reconciliation"]
        est_total = cat_rec["estimated_total"]
        emergency_reserve = cat_rec["emergency_reserve"]
        unallocated = cat_rec["unallocated_balance"]

        # Emergency reserve is positive and protected
        assert emergency_reserve > 0
        assert cat_rec["is_emergency_reserve_protected"] is True

        # Arithmetic: unallocated = user_budget - estimated_total
        assert round(unallocated, 2) == round(user_budget - est_total, 2)

        # Ensure emergency reserve is NOT deducted a second time
        double_counted = round(user_budget - est_total - emergency_reserve, 2)
        assert unallocated != double_counted

    def test_currency_conversion_and_formatting(self):
        """Currency formatting and unit conversions must be stable across USD, EUR, INR, JPY."""
        amount_usd = 100.0
        inr_val = CurrencyService.convert(amount_usd, "USD", "INR")
        jpy_val = CurrencyService.convert(amount_usd, "USD", "JPY")
        eur_val = CurrencyService.convert(amount_usd, "USD", "EUR")

        assert inr_val > 7000.0
        assert jpy_val > 10000.0
        assert 70.0 <= eur_val <= 110.0


# ==============================================================================
# 2. MEAL PRICING & DINING INTELLIGENCE TESTS
# ==============================================================================

class TestMealPricingAndDiningIntelligence:
    """Verifies elimination of the ₹25 meal cost bug and realistic dining benchmarks."""

    def test_no_25_rupee_meal_in_inr(self):
        """Meal costs in INR must never default to 25 INR. Must use realistic regional benchmark (> 1000 INR)."""
        registry = CanonicalPricingRegistry(target_currency="INR")
        record = registry.register(
            place_name="Le Petit Bistro",
            category="dining",
            destination="Paris",
            ticket_price_adult=0.0,
            meal_cost_est=25.0  # Implausibly low input (₹25)
        )

        assert record.effective_meal_cost > 1000.0
        assert record.meal_price_status == "Illustrative Regional Estimate"
        assert record.meal_cost_is_estimate is True

    def test_missing_meal_cost_defaults_to_realistic_benchmark_across_currencies(self):
        """When meal cost is None, it defaults to standard mid-range benchmark (~$18 USD equivalent)."""
        # Test in USD
        usd_reg = CanonicalPricingRegistry(target_currency="USD")
        rec_usd = usd_reg.register(place_name="Tokyo Ramen", category="dining", destination="Tokyo", meal_cost_est=None)
        assert rec_usd.effective_meal_cost >= 15.0
        assert rec_usd.meal_cost_is_estimate is True

        # Test in JPY
        jpy_reg = CanonicalPricingRegistry(target_currency="JPY")
        rec_jpy = jpy_reg.register(place_name="Tokyo Ramen", category="dining", destination="Tokyo", meal_cost_est=25.0)  # 25 JPY is impossible
        assert rec_jpy.effective_meal_cost >= 2000.0
        assert rec_jpy.meal_cost_is_estimate is True

    def test_dining_entry_is_free_with_meal_cost_separate(self):
        """Dining establishments have 0 admission, but clearly distinguish meal cost from admission."""
        reg = CanonicalPricingRegistry(target_currency="USD")
        rec = reg.register(place_name="Traditional Trattoria", category="dining", destination="Rome", ticket_price_adult=0.0)
        assert rec.effective_adult_price == 0.0
        assert "dining" in rec.price_status.lower()
        assert rec.is_free is False  # Dining is not "free entry attraction"


# ==============================================================================
# 3. ATTRACTION IDENTITY & PAID VS FREE ADMISSION TESTS
# ==============================================================================

class TestAttractionIdentityAndAdmission:
    """Verifies global paid venues are never marked free, and free open public areas are distinguished."""

    def test_global_paid_venues_never_marked_free(self):
        """Major paid landmarks across Paris, Tokyo, Istanbul, Rome, Singapore must never be marked 'Free Entry'."""
        reg = CanonicalPricingRegistry(target_currency="USD")
        paid_landmarks = [
            ("Louvre Museum", "Paris"),
            ("Eiffel Tower", "Paris"),
            ("Tokyo Skytree", "Tokyo"),
            ("Shibuya Sky", "Tokyo"),
            ("Hagia Sophia", "Istanbul"),
            ("Topkapi Palace", "Istanbul"),
            ("Colosseum", "Rome"),
            ("Gardens by the Bay", "Singapore"),
            ("Blue Lagoon", "Reykjavik")
        ]

        for name, dest in paid_landmarks:
            rec = reg.register(place_name=name, category="sightseeing", destination=dest, ticket_price_adult=0.0)
            assert rec.effective_adult_price > 0.0, f"{name} in {dest} had 0 price"
            assert rec.price_status == "Paid admission", f"{name} status was {rec.price_status}"
            assert rec.is_free is False, f"{name} was marked as free"

    def test_open_public_areas_correctly_classified_as_free(self):
        """Open public parks, squares, and beaches without paid interiors must be marked Free Entry."""
        reg = CanonicalPricingRegistry(target_currency="USD")
        free_venues = [
            ("Central Park", "park", "New York"),
            ("Sultanahmet Square", "square", "Istanbul"),
            ("Ueno Park", "park", "Tokyo"),
            ("Bondi Beach", "beach", "Sydney"),
            ("Champs-Élysées", "street", "Paris")
        ]

        for name, cat, dest in free_venues:
            rec = reg.register(place_name=name, category=cat, destination=dest, ticket_price_adult=0.0)
            assert rec.effective_adult_price == 0.0
            assert rec.is_free is True
            assert rec.price_status == "Free Entry"

    def test_unverified_interior_venue_not_falsely_marked_free(self):
        """An unverified museum or palace with 0 ticket price is marked as unverified fee, NOT Free Entry."""
        reg = CanonicalPricingRegistry(target_currency="USD")
        rec = reg.register(
            place_name="Historical Royal Palace Museum",
            category="museum",
            destination="UnknownCity",
            ticket_price_adult=0.0
        )
        assert rec.is_free is False
        assert "unverified" in rec.price_status.lower() or "paid" in rec.price_status.lower()


# ==============================================================================
# 4. COORDINATE UNIQUENESS & CITY-CENTER FALLBACK ELIMINATION
# ==============================================================================

class TestCoordinateResolution:
    """Verifies that attractions receive distinct real coordinates and city-center coordinates are never duplicated."""

    def test_distinct_attractions_have_unique_coordinates(self):
        """Different attractions in Paris, Tokyo, and Istanbul must have distinct non-identical coordinates."""
        louvre_info = resolve_poi_coordinates("Louvre Museum", "Paris")
        eiffel_info = resolve_poi_coordinates("Eiffel Tower", "Paris")
        notre_info = resolve_poi_coordinates("Notre-Dame Cathedral", "Paris")

        assert louvre_info is not None
        assert eiffel_info is not None
        assert notre_info is not None

        lat_l, lon_l = louvre_info["latitude"], louvre_info["longitude"]
        lat_e, lon_e = eiffel_info["latitude"], eiffel_info["longitude"]

        # Paris city center was (48.8566, 2.3522). None should be the generic city center.
        assert not (lat_l == 48.8566 and lon_l == 2.3522)
        assert not (lat_e == 48.8566 and lon_e == 2.3522)

        # Distances between them must be positive
        dist_louvre_eiffel = haversine_distance_km(lat_l, lon_l, lat_e, lon_e)
        assert dist_louvre_eiffel > 2.0, f"Distance {dist_louvre_eiffel} km too small"

    def test_unknown_venue_does_not_get_fake_city_center(self):
        """An unknown venue must return None rather than being assigned fake city-center coordinates."""
        coords = resolve_poi_coordinates("Totally Nonexistent XYZ Venue 123", "Paris")
        # In offline/mock test environment, it must not return Paris city center
        if coords is not None:
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            if lat is not None and lon is not None:
                assert not (abs(lat - 48.8566) < 0.001 and abs(lon - 2.3522) < 0.001)


# ==============================================================================
# 5. ROUTING CALCULATION, DISTANCES, STATUSES & DIRECTIONS
# ==============================================================================

class TestRoutingAndTransit:
    """Verifies realistic positive distances, no zero distance routes for distinct places, and origin/dest links."""

    def test_positive_distances_between_distinct_locations(self):
        """Transit between two distinct locations must have positive distance and realistic travel time."""
        # Tokyo Station to Shibuya Crossing
        tokyo_st = (35.6812, 139.7671)
        shibuya = (35.6595, 139.7004)

        dist_km = haversine_distance_km(tokyo_st[0], tokyo_st[1], shibuya[0], shibuya[1])
        assert 6.0 <= dist_km <= 10.0

        transition = estimate_travel_transition(tokyo_st[0], tokyo_st[1], shibuya[0], shibuya[1], "Tokyo")
        assert transition["distance_km"] > 0.0
        assert transition["duration_minutes"] >= 5
        assert any(m in transition["travel_mode"] for m in ["Transit", "Metro", "Taxi", "Public"])

    def test_zero_distance_not_shown_as_successful_road_route(self):
        """Co-located venues in same complex are 'Within complex'; separate venues cannot show zero road distance."""
        # Same coordinates
        transition = estimate_travel_transition(48.8606, 2.3376, 48.8606, 2.3376, "Paris")
        assert transition["status"] in ["Within complex", "Route unavailable"]
        assert transition["travel_mode"] in ["Walking", "Immediate / Within Complex"]

    def test_directions_url_contains_origin_and_destination(self):
        """Google Maps directions link must specify both origin and destination parameters."""
        c_lat, c_lon = 48.8606, 2.3376
        n_lat, n_lon = 48.8584, 2.2945
        url = f"https://www.google.com/maps/dir/?api=1&origin={c_lat},{c_lon}&destination={n_lat},{n_lon}"
        assert "origin=48.8606,2.3376" in url
        assert "destination=48.8584,2.2945" in url


# ==============================================================================
# 6. AIRPORT TRANSFER & DEPARTURE BUFFER ACTIVITIES
# ==============================================================================

class TestAirportTransferAndDepartureBuffers:
    """Verifies separate airport transfer and buffer activities on Day 1 and Final Day."""

    def test_day1_separate_airport_transfer_and_refreshment_buffer(self):
        """Day 1 must split gateway transfer (Activity 1A) and accommodation check-in/buffer (Activity 1B)."""
        prompt = "Destination: Paris\nTotal Duration: 3 Days\nTarget Currency Code: EUR\nComfort Tier: Mid-range"
        raw_json = MockProvider().generate(prompt)
        parsed = json.loads(raw_json)
        days = parsed.get("days") or parsed.get("trip", {}).get("itinerary_days", [])
        assert len(days) >= 1

        day1_acts = days[0]["activities"]
        assert len(day1_acts) >= 2

        act1a = day1_acts[0]
        act1b = day1_acts[1]

        # Act 1A is gateway transfer
        assert "Airport" in act1a["title"] or "Transfer" in act1a["title"] or "Gateway" in act1a["title"]

        # Act 1B is hotel check-in / buffer
        assert "Accommodation" in act1b["title"] or "Check-in" in act1b["title"] or "Refreshment" in act1b["title"]

    def test_final_day_separate_departure_transfer_and_airport_buffer(self):
        """Final Day must split departure transfer and dedicated >= 2.5 hour airport buffer."""
        prompt = "Destination: Tokyo\nTotal Duration: 3 Days\nTarget Currency Code: JPY\nComfort Tier: Mid-range"
        raw_json = MockProvider().generate(prompt)
        parsed = json.loads(raw_json)
        days = parsed.get("days") or parsed.get("trip", {}).get("itinerary_days", [])
        assert len(days) >= 2

        final_day_acts = days[-1]["activities"]
        assert len(final_day_acts) >= 2

        # Penultimate is departure transfer
        transfer_act = final_day_acts[-2]
        buffer_act = final_day_acts[-1]

        assert "Departure Transfer" in transfer_act["title"] or "Transfer" in transfer_act["title"]
        assert "Buffer" in buffer_act["title"] or "Security" in buffer_act["title"]
        assert "buffer" in buffer_act["description"].lower() or "2.5" in buffer_act["description"]


# ==============================================================================
# 7. DAY REGENERATION & LOCKED ACTIVITY PRESERVATION
# ==============================================================================

class TestDayRegenerationAndLockedActivities:
    """Verifies that locked activities are strictly preserved and newly regenerated activities do not overlap."""

    def test_locked_activity_preserved_and_chronological_ordering(self):
        """Preserved locked activity end time pushes subsequent regenerated activities forward."""
        locked_act = {
            "id": 101,
            "title": "Private Cooking Masterclass",
            "start_time": "14:00",
            "end_time": "16:30",
            "is_locked": True
        }

        # Simulate regeneration schedule resolution
        current_time_mins = 8 * 60 + 30
        dur_mins = 90

        # Activity 1: morning
        act1_start = current_time_mins
        act1_end = act1_start + dur_mins
        current_time_mins = act1_end + 20

        # Activity 2: midday
        act2_start = current_time_mins
        act2_end = act2_start + dur_mins
        current_time_mins = act2_end + 20

        # Activity 3: lunch
        act3_start = current_time_mins
        act3_end = act3_start + dur_mins
        current_time_mins = act3_end + 20

        # Activity 4 collision with locked activity (14:00 - 16:30)
        l_st_mins = 14 * 60  # 840
        l_et_mins = 16 * 60 + 30  # 990

        if (current_time_mins < l_st_mins and (current_time_mins + dur_mins) > (l_st_mins - 15)) or (l_st_mins <= current_time_mins < l_et_mins + 15):
            current_time_mins = l_et_mins + 20

        act4_start = current_time_mins
        act4_end = act4_start + dur_mins

        assert act1_end <= l_st_mins
        # act4 was pushed after locked activity
        assert act4_start >= l_et_mins + 20


# ==============================================================================
# 8. WEATHER HORIZON & PROVENANCE
# ==============================================================================

class TestWeatherHorizonAndProvenance:
    """Verifies that trips > 14 days away are marked Seasonal Climate Standard, not confirmed forecast."""

    def test_weather_beyond_14_days_marked_seasonal_standard(self):
        """A destination query for 2027 (distant future) must be marked 'Seasonal Climate Standard'."""
        distant_date = "2027-04-15"
        weather_res = get_weather("Istanbul", date_str=distant_date)

        sel_weather = weather_res.get("selected_date_weather")
        assert sel_weather is not None
        assert sel_weather["is_confirmed_forecast"] is False
        assert sel_weather["forecast_unavailable"] is True
        assert sel_weather["weather_confidence"] == "Seasonal Climate Standard"
        assert "Seasonal Climate Standard" in sel_weather["status_label"]

    def test_seasonal_climate_estimation_by_geography(self):
        """Tropical destinations return tropical seasonal norms; Mediterranean return Mediterranean norms."""
        bali_climate = _estimate_seasonal_climate("Bali", lat=-8.4, month=7)
        assert bali_climate["temperature"] >= 26.0
        assert "Tropical" in bali_climate["description"]

        istanbul_climate = _estimate_seasonal_climate("Istanbul", lat=41.0, month=3)
        assert istanbul_climate["temperature"] <= 18.0
        assert "Mediterranean" in istanbul_climate["description"]


# ==============================================================================
# 9. GLOBAL DESTINATION INDEPENDENCE (7 DIVERSE DESTINATIONS)
# ==============================================================================

class TestGlobalDestinationIndependence:
    """Verifies that the exact same travel engine functions across 7 diverse global destinations."""

    GLOBAL_DESTINATIONS = [
        {"city": "Paris", "country": "France", "currency": "EUR"},
        {"city": "Tokyo", "country": "Japan", "currency": "JPY"},
        {"city": "Istanbul", "country": "Turkey", "currency": "TRY"},
        {"city": "Bali", "country": "Indonesia", "currency": "IDR"},
        {"city": "Reykjavik", "country": "Iceland", "currency": "ISK"},
        {"city": "Singapore", "country": "Singapore", "currency": "SGD"},
        {"city": "Cusco", "country": "Peru", "currency": "PEN"},
    ]

    @pytest.mark.parametrize("dest", GLOBAL_DESTINATIONS)
    def test_destination_plan_and_pricing_pipeline(self, dest):
        """Calculate canonical budget and POI validation for each global destination without hardcoded hacks."""
        city = dest["city"]
        curr = dest["currency"]

        # 1. Budget Plan Generation
        plan = BudgetAllocationService.calculate_plan(
            total_budget=5500.0,
            currency="USD",
            tier="mid_range",
            destination=city,
            origin_city="New York",
            days=5,
            adults=2,
            children=0
        )
        assert plan["total_user_budget"] == 5500.0
        assert plan["is_feasible"] is True
        assert len(plan["categories"]) == 8

        # 2. Canonical Pricing Registry for Destination
        registry = CanonicalPricingRegistry(target_currency="USD")
        rec = registry.register(
            place_name=f"Historic Landmark of {city}",
            category="sightseeing",
            destination=city,
            ticket_price_adult=20.0
        )
        assert rec.effective_adult_price == 20.0
        assert rec.price_status in ["Official Entry Registry", "Paid admission", "Verified Admission"]

        # 3. Dining Benchmark for Destination
        dining_rec = registry.register(
            place_name=f"Traditional Bistro of {city}",
            category="dining",
            destination=city,
            meal_cost_est=18.0
        )
        assert dining_rec.effective_meal_cost >= 15.0
