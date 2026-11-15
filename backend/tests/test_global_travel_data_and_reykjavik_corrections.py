"""
test_global_travel_data_and_reykjavik_corrections.py — Automated Regression Test Suite
Validates the global architecture upgrades addressing the Reykjavik test:
1. International Airport Resolution: KEF over domestic RKV on international routes; ~49 km ground transfer.
2. Weather Intelligence: Dynamic seasonal climate standards for >14 days (March Reykjavik ~0.5°C flurries, NOT 26°C).
3. Attraction Discovery & Ground Truth Pricing: FlyOver Iceland (5,490 ISK) and Icelandic Lava Show (6,490 ISK) paid.
4. Realistic Activity Durations: 30 to 90 minutes (no arbitrary 150-minute blocks for sights).
5. Dining Partitioning: Exclusion of restaurants/cafes from daytime attraction slots.
6. Distance-Calibrated International Flights: Long-haul flights calibrated by origin-destination route distance.
7. Budget Transparency: Remaining Balance = User Budget - Estimated Total Trip Cost - Recorded Expenses.
8. Location Deduplication: Elimination of repetitive country naming (e.g. "Reykjavík, Iceland, Iceland").
"""

import os
import sys
import json
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

from app.services.transit.airport_service import (
    resolve_serving_airports,
    get_primary_gateway_airport
)
from app.services.transit.providers.flight_provider import FlightProvider
from app.routes.weather import get_weather, _estimate_seasonal_climate
from app.services.weather.openmeteo_service import get_openmeteo_weather, get_seasonal_climate_standard
from app.services.pricing.canonical_pricing_registry import CanonicalPricingRegistry, KNOWN_PAID_VENUES
from app.services.poi_service import get_realistic_activity_duration, fetch_real_pois_for_destination
from app.services.budget_allocation_service import BudgetAllocationService
from app.services.location.location_normalizer import resolve_destination_info
from app.ai.providers.mock_provider import MockProvider


# ==============================================================================
# 1. INTERNATIONAL AIRPORT RESOLUTION TESTS
# ==============================================================================

class TestAirportResolutionAndGroundTransfer:
    """Verifies that international gateways are distinguished from domestic airfields globally."""

    def test_reykjavik_international_resolves_to_kef(self):
        """International route to Reykjavik must resolve to Keflavík (KEF), NOT Reykjavík Airport (RKV)."""
        # Central Reykjavik coordinates
        lat, lon = 64.1466, -21.9426
        serving = resolve_serving_airports("Reykjavik", lat, lon, is_international=True)
        assert len(serving) >= 1
        primary = serving[0]
        assert primary["iata"] == "KEF", f"Expected KEF as primary international gateway, got {primary['iata']}"
        assert primary["tier"] in ["primary_international", "secondary_international"]
        assert "Keflavík" in primary["name"] or "Keflavik" in primary["name"]

    def test_reykjavik_ground_transfer_distance_and_duration(self):
        """Ground transfer from KEF to central Reykjavik must reflect real road corridor (~48-50 km, 40-50 mins)."""
        lat, lon = 64.1466, -21.9426
        gateway = get_primary_gateway_airport("Reykjavik", lat, lon, is_international=True)
        assert gateway["iata"] == "KEF"
        # Highway Reykjanesbraut road distance is ~47-52 km
        assert 45.0 <= gateway["distance_km"] <= 55.0, f"Expected ~49 km, got {gateway['distance_km']} km"
        assert 40 <= gateway["transfer_duration_minutes"] <= 60, f"Expected 40-60 min transfer, got {gateway['transfer_duration_minutes']}"

    def test_domestic_vs_international_flight_provider_selection(self):
        """FlightProvider must select KEF for international long-distance route and RKV only for domestic flights."""
        from app.services.transit.providers.flight_provider import find_nearest_airport
        lat, lon = 64.1466, -21.9426
        # International flight from India or Europe (>500 km)
        intl_airport = find_nearest_airport(lat, lon, is_international=True)
        assert intl_airport is not None
        assert intl_airport["iata"] == "KEF", f"Expected KEF for international, got {intl_airport['iata']}"

        # Domestic flight within Iceland (<500 km)
        dom_airport = find_nearest_airport(lat, lon, is_international=False)
        assert dom_airport is not None
        assert dom_airport["iata"] == "RKV", f"Expected RKV for domestic, got {dom_airport['iata']}"

    @pytest.mark.parametrize("dest,lat,lon,expected_iatas", [
        ("Paris", 48.8566, 2.3522, ["CDG", "ORY"]),
        ("Tokyo", 35.6762, 139.6503, ["HND", "NRT"]),
        ("New York", 40.7128, -74.0060, ["JFK", "EWR"]),
        ("Istanbul", 41.0082, 28.9784, ["IST", "SAW"]),
        ("Singapore", 1.3521, 103.8198, ["SIN"]),
        ("Bali", -8.4095, 115.1889, ["DPS"]),
        ("Tromso", 69.6492, 18.9553, ["TOS"]),
    ])
    def test_global_international_gateways(self, dest, lat, lon, expected_iatas):
        """Global test: International routes worldwide must resolve to a verified primary international airport."""
        gateway = get_primary_gateway_airport(dest, lat, lon, is_international=True)
        assert gateway["iata"] in expected_iatas, f"For {dest}, expected one of {expected_iatas}, got {gateway['iata']}"


# ==============================================================================
# 2. WEATHER INTELLIGENCE & 26°C ELIMINATION TESTS
# ==============================================================================

class TestWeatherIntelligenceAndSeasonalClimate:
    """Verifies scientific climate estimates for >14 days and elimination of hardcoded 26°C."""

    def test_reykjavik_march_seasonal_climate(self):
        """Reykjavik in March must reflect sub-arctic climate (~0.5°C with snow flurries), NOT 26°C."""
        climate = _estimate_seasonal_climate("Reykjavik", lat=64.1466, month=3)
        assert climate["temperature"] < 3.0, f"Reykjavik March temperature should be near 0°C, got {climate['temperature']}°C"
        assert "26" not in str(climate["temperature"])
        assert "sub-arctic" in climate["description"].lower() or "winter" in climate["description"].lower() or "snow" in climate["description"].lower()

    def test_distant_date_returns_seasonal_climate_standard(self):
        """Trip scheduled > 14 days in future must be labeled 'Seasonal Climate Standard' with provenance."""
        resp = get_weather("Reykjavik", date_str="2027-03-15")
        assert resp["is_seasonal_estimate"] is True
        assert resp["weather_confidence"] == "Seasonal Climate Standard"
        assert "Historical" in resp["provider"]
        cur = resp["current"]
        assert cur["temperature"] < 5.0
        assert "26" not in str(cur["temperature"])

    def test_polar_latitude_classification(self):
        """Polar latitudes (>60°N) must receive sub-arctic seasonal curves."""
        # Tromsø, Norway (69.6°N) in January
        tromso_jan = get_seasonal_climate_standard(69.6492, 18.9553, "Tromsø", target_date="2027-01-20")
        assert tromso_jan["temp_c"] <= 0.0
        assert tromso_jan["weather_confidence"] == "Seasonal Climate Standard"

        # Tromsø in July
        tromso_jul = get_seasonal_climate_standard(69.6492, 18.9553, "Tromsø", target_date="2027-07-20")
        assert 10.0 <= tromso_jul["temp_c"] <= 16.0


# ==============================================================================
# 3. ATTRACTION DISCOVERY, PRICING & REALISTIC DURATIONS
# ==============================================================================

class TestAttractionDiscoveryAndDurations:
    """Verifies ground truth pricing (FlyOver & Lava Show), realistic durations (no 150-min blocks), and dining separation."""

    def test_flyover_iceland_and_lava_show_paid_pricing(self):
        """FlyOver Iceland and Lava Show must be verified paid attractions in canonical registry."""
        registry = CanonicalPricingRegistry(target_currency="ISK")
        flyover = registry.register(name="FlyOver Iceland", destination="Reykjavik", category="Sightseeing", source_currency="ISK")
        assert flyover.is_free is False
        assert flyover.adult_price == 5490.0, f"Expected 5490 ISK, got {flyover.adult_price}"

        lava = registry.register(name="Icelandic Lava Show Reykjavik", destination="Reykjavik", category="Museum", source_currency="ISK")
        assert lava.is_free is False
        assert lava.adult_price == 6490.0, f"Expected 6490 ISK, got {lava.adult_price}"

    def test_realistic_activity_durations_scale(self):
        """Experience durations must be calibrated (30 to 90 mins), not arbitrary 150-minute blocks."""
        assert get_realistic_activity_duration("FlyOver Iceland") == 45
        assert get_realistic_activity_duration("Icelandic Lava Show Reykjavik") == 50
        assert get_realistic_activity_duration("Hallgrímskirkja Church & Tower") == 45
        assert get_realistic_activity_duration("Sun Voyager Waterfront Sculpture") == 30
        assert get_realistic_activity_duration("National Museum of Iceland") == 90
        assert get_realistic_activity_duration("Sandholt Artisan Bakery") == 45
        assert get_realistic_activity_duration("Messinn Seafood Restaurant") == 60

    def test_dining_venues_strictly_partitioned_from_attraction_slots(self):
        """Restaurants and cafes must not be selected as daytime sightseeing attraction slots."""
        mock_provider = MockProvider()
        prompt = (
            "Generate Itinerary\n"
            "Destination: Reykjavik\n"
            "Origin City: Coimbatore\n"
            "Dates: 2027-03-15 to 2027-03-18\n"
            "Travelers: 2 adults\n"
            "Budget: 400000 INR\n"
            "Travel Style: luxury\n"
            "Selected Activity Interests: Culture, Sightseeing\n"
        )
        raw_res = mock_provider.generate(prompt)
        itinerary = json.loads(raw_res)
        days = itinerary.get("trip", {}).get("itinerary_days", []) or itinerary.get("itinerary_days", [])
        assert len(days) >= 2

        for day in days:
            acts = day.get("activities", [])
            morning_and_afternoon = [a for a in acts if a.get("time_slot") in ["morning", "afternoon"] and a.get("activity_type") == "attraction"]
            for a in morning_and_afternoon:
                title_low = a["title"].lower()
                assert not any(w in title_low for w in ["restaurant", "cafe", "café", "bakery", "bistro", "ramen"]), \
                    f"Attraction slot contains dining venue: {a['title']}"


# ==============================================================================
# 4. DISTANCE-CALIBRATED FLIGHT ESTIMATES & BUDGET TRANSPARENCY
# ==============================================================================

class TestBudgetAndFlightDistanceCalibration:
    """Verifies distance-calibrated flight costs and remaining balance accounting."""

    def test_distance_calibrated_flight_costs(self):
        """Flight estimates must scale with route distance rather than receiving identical flat amounts."""
        def extract_flight_estimate(plan):
            cats = plan.get("category_reconciliation", {}).get("categories", {})
            out_c = cats.get("outbound_transport", {}).get("estimated", 0.0)
            ret_c = cats.get("return_transport", {}).get("estimated", 0.0)
            return out_c + ret_c

        # Regional International: Coimbatore -> Singapore (~3,300 km)
        plan_singapore = BudgetAllocationService.calculate_plan(
            total_budget=300000,
            currency="INR",
            tier="mid_range",
            destination="Singapore",
            origin_city="Coimbatore",
            days=5,
            adults=2,
            children=0
        )
        singapore_trans = extract_flight_estimate(plan_singapore)

        # Long-Haul: Coimbatore -> Reykjavik (~8,600 km)
        plan_reykjavik = BudgetAllocationService.calculate_plan(
            total_budget=500000,
            currency="INR",
            tier="mid_range",
            destination="Reykjavik",
            origin_city="Coimbatore",
            days=5,
            adults=2,
            children=0
        )
        reykjavik_trans = extract_flight_estimate(plan_reykjavik)

        # Ultra Long-Haul: Coimbatore -> New York (~13,500 km)
        plan_ny = BudgetAllocationService.calculate_plan(
            total_budget=600000,
            currency="INR",
            tier="mid_range",
            destination="New York",
            origin_city="Coimbatore",
            days=5,
            adults=2,
            children=0
        )
        ny_trans = extract_flight_estimate(plan_ny)

        # Flight cost must strictly follow distance tier: Singapore < Reykjavik < New York
        assert singapore_trans < reykjavik_trans, f"Singapore flights ({singapore_trans}) should be cheaper than Reykjavik ({reykjavik_trans})"
        assert reykjavik_trans < ny_trans, f"Reykjavik flights ({reykjavik_trans}) should be cheaper than New York ({ny_trans})"

    def test_canonical_accounting_formula(self):
        """Remaining balance must equal Total Budget - Estimated Total Trip Cost."""
        total_b = 500000.0
        plan = BudgetAllocationService.calculate_plan(
            total_budget=total_b,
            currency="INR",
            tier="mid_range",
            destination="Reykjavik",
            origin_city="Coimbatore",
            days=7,
            adults=2,
            children=1
        )
        est_cost = plan["total_estimated_trip_cost"]
        unallocated = plan["unallocated_balance"]
        # Expected formula: unallocated = total_budget - total_estimated_trip_cost
        assert round(unallocated, 2) == round(total_b - est_cost, 2)
        assert unallocated != total_b, "Unallocated balance should never equal original budget when estimated cost > 0"


# ==============================================================================
# 5. LOCATION FORMATTING DEDUPLICATION
# ==============================================================================

class TestLocationFormattingDeduplication:
    """Verifies that location formatting never renders duplicate country names."""

    def test_weather_and_trip_destination_deduplication(self):
        """'Reykjavík, Iceland' + 'Iceland' must not become 'Reykjavík, Iceland, Iceland'."""
        weather_res = get_weather("Reykjavik", date_str="2027-03-15")
        title = weather_res.get("destination_title", "")
        # Should be "Reykjavík, Iceland" or "Reykjavik, Iceland", never duplicated
        assert title.lower().count("iceland") <= 1, f"Repeated country name in destination title: {title}"

        dest_info = resolve_destination_info("Reykjavík, Iceland", "Coimbatore")
        clean_name = dest_info.get("destination_clean")
        assert clean_name.lower().count("iceland") <= 1
