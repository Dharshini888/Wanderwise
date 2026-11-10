"""
test_e2e_trip_pipeline.py — End-to-End Verification of AI Itinerary Generation, Budgeting,
Preferences, Transportation, Geographic Feasibility, Real Places, Dietary Accuracy, and Scheduling.
"""

import os
import sys
import io
import json
from datetime import date, datetime

# Ensure utf-8 output encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Force SQLite test database and mock AI provider for sandbox execution
os.environ["DATABASE_URL"] = "sqlite:///./test_itinerary.db"
os.environ["AI_PROVIDER"] = "mock"
os.environ["AI_DEFAULT_PROVIDER"] = "mock"
os.environ["AI_FALLBACK_PROVIDER"] = "mock"

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.place import Place
from app.models.expense import Expense
from app.services.budget_allocation_service import BudgetAllocationService, TIER_STRATEGIES
from app.services.trip_service import enrich_trip_response, get_today_itinerary
from app.services.ai_service import generate_structured_itinerary
from app.routes.trips import resolve_trip_preferences, _populate_trip_itinerary_from_ai
from app.services.route_optimizer import haversine_distance_km

FORBIDDEN_MEAT_KEYWORDS = [
    "anticucho", "sandwich de chola", "chairo", "beef", "pork", "chicken",
    "meat", "lamb", "fish", "seafood", "steak", "poultry", "bacon"
]

GENERIC_PLACEHOLDERS = [
    "scenic walk & artisan trail",
    "scenic overlook & panoramic vistas",
    "regional culinary lunch",
    "artisan trail near",
    "panoramic vistas:",
    "culinary lunch near"
]


def run_all_tests():
    print("=" * 80)
    print("🚀 STARTING COMPREHENSIVE END-TO-END VERIFICATION (11 AUDIT CRITERIA)")
    print("=" * 80)

    # 1. Initialize SQLite Database
    engine = create_engine("sqlite:///./test_itinerary.db", echo=False)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create test user with Vegetarian dietary preference
    user = User(
        email="traveler@example.com",
        name="Explorer User",
        currency="INR",
        preferred_budget="mid_range",
        preferred_activities="Local Culture, Beaches, Hidden Gems",
        dietary_preferences="Vegetarian",
        preferred_climate="temperate"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ Step 1: Test user created with ID {user.id}, currency INR, tier mid_range, dietary: Vegetarian")

    # 2. Test Budget Comfort Tier Allocations across all 4 tiers
    print("\n" + "=" * 80)
    print("📊 Step 2: Testing Centralized Budget Allocation Service (4 Tiers)")
    print("=" * 80)

    total_test_budget = 150000.0
    tiers_to_test = ["budget", "mid_range", "luxury", "ultra_luxury"]
    tier_plans = {}

    for t in tiers_to_test:
        plan = BudgetAllocationService.calculate_plan(
            total_budget=total_test_budget,
            currency="INR",
            tier=t,
            destination="Bolivia",
            origin_city="Coimbatore",
            days=5,
            adults=1,
            children=0,
            travel_style="solo",
            transport_mode="Mixed Transport",
            accommodation_preference="hotel"
        )
        tier_plans[t] = plan
        cat_map = {c["key"]: c for c in plan["categories"]}
        cat_sum = sum(c["amount"] for c in plan["categories"])
        print(f"\n  Tier: {plan['tier_name']} ({t})")
        print(f"    Total User Budget: ₹{plan['total_user_budget']:,.2f} | Sum of Categories: ₹{cat_sum:,.2f}")
        for c in plan["categories"]:
            print(f"    {c['label']}: ₹{c['amount']:,.2f} ({c['percentage']}%)")

        # Verify exact sum to budget
        assert round(cat_sum, 2) == round(total_test_budget, 2), f"Tier {t} sum mismatch: {cat_sum} != {total_test_budget}"

    # Verify that changing budget comfort tier produces DIFFERENT allocations
    lodging_budget = next(c["percentage"] for c in tier_plans["budget"]["categories"] if c["key"] == "accommodation")
    lodging_mid = next(c["percentage"] for c in tier_plans["mid_range"]["categories"] if c["key"] == "accommodation")
    lodging_lux = next(c["percentage"] for c in tier_plans["luxury"]["categories"] if c["key"] == "accommodation")
    lodging_ultra = next(c["percentage"] for c in tier_plans["ultra_luxury"]["categories"] if c["key"] == "accommodation")

    assert lodging_budget != lodging_mid, "Budget and Mid-range lodging % should differ!"
    assert lodging_mid != lodging_lux, "Mid-range and Luxury lodging % should differ!"
    assert lodging_lux != lodging_ultra, "Luxury and Ultra Luxury lodging % should differ!"
    print("\n✅ Step 2 PASSED: All 4 tiers produce distinct, explainable, 100% exact allocations!")

    # 3. Simulate Complete 14-Step Wizard Input Payload (Scenario from Prompt)
    print("\n" + "=" * 80)
    print("📝 Step 3: Simulating 14-Step Wizard Input & Preference Resolution")
    print("=" * 80)

    wizard_payload = {
        "destination": "Bolivia",
        "country": "Bolivia",
        "origin_city": "Coimbatore",
        "origin_airport": "CJB",
        "destination_airport": "LPB",
        "visa_status": "Visa upon arrival",
        "start_date": "2026-11-06",
        "end_date": "2026-11-10",
        "flexible_dates": "Fixed Dates",
        "travel_type": "leisure",
        "travel_style": "solo",
        "adults": 1,
        "children": 0,
        "seniors": 0,
        "pets": 0,
        "budget": 150000.0,
        "currency": "INR",
        "budget_type": "Mid-range",
        "interests": "Local Culture, Beaches, Hidden Gems",
        "food_preferences": "Vegetarian",
        "food_allergies": "None",
        "accommodation_preference": "hotel",
        "transportation": "mixed",
        "activity_pace": "balanced",
        "accessibility": "Standard",
        "ai_preferences": "avoid_crowds,hidden_gems",
        "wake_up_time": "08:00",
        "sleep_time": "22:30",
        "lunch_time": "13:00",
        "dinner_time": "19:30",
        "preferred_sunset_spot": "viewpoint",
        "weather_preference": "temperate"
    }

    from app.schemas.trip_schemas import TripCreate

    trip_create_obj = TripCreate(
        user_id=user.id,
        destination="Bolivia",
        country="Bolivia",
        origin_city="Coimbatore",
        origin_airport="CJB",
        destination_airport="LPB",
        start_date=date(2026, 11, 6),
        end_date=date(2026, 11, 10),
        budget=150000.0,
        currency="INR",
        travel_style="solo",
        transportation="mixed",
        accommodation_preference="hotel",
        interests="Local Culture, Beaches, Hidden Gems",
        trip_preferences=wizard_payload
    )

    resolved_prefs = resolve_trip_preferences(
        data=trip_create_obj,
        current_user=user
    )

    print("Resolved Preferences Verification:")
    print(f"  Destination: {trip_create_obj.destination}")
    print(f"  Origin: {resolved_prefs['origin_city']}")
    print(f"  Budget: ₹{trip_create_obj.budget:,.2f} {resolved_prefs['currency']}")
    print(f"  Budget Tier: {resolved_prefs['budget_tier']}")
    print(f"  Transportation: '{resolved_prefs['transportation']}'")
    print(f"  Accommodation: {resolved_prefs['accommodation_preference']}")
    print(f"  Interests: {resolved_prefs['interests']}")
    print(f"  Dietary: {resolved_prefs['dietary_preferences']}")
    print(f"  AI Directives: {resolved_prefs['ai_preferences']}")

    assert resolved_prefs["transportation"] == "Mixed Transport", f"Expected 'Mixed Transport', got {resolved_prefs['transportation']}"
    assert trip_create_obj.budget == 150000.0
    assert resolved_prefs["currency"] == "INR"
    assert "hidden_gems" in resolved_prefs["ai_preferences"]
    assert "Vegetarian" in resolved_prefs["dietary_preferences"]
    print("✅ Step 3 PASSED: Preference resolution preserved all wizard selections!")

    # 4. Create Trip DB Record
    print("\n" + "=" * 80)
    print("💾 Step 4: Creating Trip in DB & Generating Structured Itinerary")
    print("=" * 80)

    trip = Trip(
        user_id=user.id,
        title="Adventure to Bolivia",
        destination=trip_create_obj.destination,
        country=trip_create_obj.country,
        origin_city=resolved_prefs["origin_city"],
        origin_airport=resolved_prefs["origin_airport"],
        destination_airport=resolved_prefs["destination_airport"],
        start_date=date(2026, 11, 6),
        end_date=date(2026, 11, 10),
        budget=trip_create_obj.budget,
        currency=resolved_prefs["currency"],
        travel_type=trip_create_obj.travel_type,
        travel_style=resolved_prefs["travel_style"],
        transportation=resolved_prefs["transportation"],
        accommodation_preference=resolved_prefs["accommodation_preference"],
        interests=resolved_prefs["interests"],
        group_size=1,
        trip_preferences=resolved_prefs["trip_preferences"],
        status="Planned"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    print(f"✅ Trip record created: ID={trip.id}, Dates={trip.start_date} to {trip.end_date}, Mode={trip.transportation}")

    # 5. Generate Structured Itinerary via AI Engine
    ai_itinerary = generate_structured_itinerary(
        destination=trip.destination,
        days=5,
        budget=float(trip.budget),
        interests=trip.interests,
        travel_style=trip.travel_style,
        group_size=1,
        currency=trip.currency,
        country=trip.country,
        origin_city=trip.origin_city,
        origin_airport=trip.origin_airport,
        destination_airport=trip.destination_airport,
        accommodation_preference=trip.accommodation_preference,
        transportation=trip.transportation,
        travel_companion="solo",
        start_date="2026-11-06",
        end_date="2026-11-10",
        trip_preferences=resolved_prefs
    )

    days_generated = ai_itinerary.get("days", [])
    print(f"Generated Days Count: {len(days_generated)}")
    assert len(days_generated) == 5, f"Expected 5 days, got {len(days_generated)}"

    # 6. Populate DB Models via _populate_trip_itinerary_from_ai
    _populate_trip_itinerary_from_ai(db, trip, ai_itinerary)
    db.commit()

    # 7. Comprehensive Verification of Persisted Days & Activities
    print("\n" + "=" * 80)
    print("🔍 Step 5: Auditing Persisted Itinerary against 11 Specific Criteria")
    print("=" * 80)

    persisted_days = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip.id).order_by(ItineraryDay.day_number.asc()).all()
    assert len(persisted_days) == 5, f"Expected 5 persisted days in DB, found {len(persisted_days)}"

    # Expected base cities & overnight stays
    expected_bases = {
        1: ("La Paz", "La Paz Central Boutique Hotel"),
        2: ("La Paz", "La Paz Central Boutique Hotel"),
        3: ("Copacabana", "Copacabana Lakefront Hotel"),
        4: ("La Paz", "La Paz Central Boutique Hotel"),
        5: ("La Paz", "Departure")
    }

    total_activities_count = 0
    lake_titicaca_found = False
    intercity_transfers_found = 0
    vegetarian_meals_checked = 0
    sunset_activities_checked = 0

    for d in persisted_days:
        acts = db.query(ItineraryActivity).filter(ItineraryActivity.day_id == d.id).order_by(ItineraryActivity.order_index.asc()).all()
        print(f"\n  Day {d.day_number} ({d.date}): '{d.title}'")
        print(f"    Theme / Note: {d.theme_note}")
        assert len(acts) >= 3, f"Day {d.day_number} has insufficient activities: {len(acts)}"
        total_activities_count += len(acts)

        # Check Base City & Overnight Stay in theme note
        exp_base, exp_overnight = expected_bases[d.day_number]
        assert exp_base.lower() in d.theme_note.lower(), f"Day {d.day_number} theme_note should mention base city '{exp_base}'"
        assert exp_overnight.lower() in d.theme_note.lower() or "departure" in exp_overnight.lower(), f"Day {d.day_number} should mention overnight stay '{exp_overnight}'"

        prev_act = None
        for a in acts:
            meta = a.activity_metadata or {}
            print(f"    [{a.start_time}-{a.end_time}] {a.title} ({a.time_slot}) | Type: {meta.get('activity_type')} | Transport: {a.transport_mode}")

            # Criterion 2: No generic placeholders
            title_lower = a.title.lower()
            for ph in GENERIC_PLACEHOLDERS:
                assert ph not in title_lower, f"Generic placeholder '{ph}' found in activity '{a.title}'"

            # Criterion 3 & 4: Geographic feasibility & Intercity Transfers
            if prev_act:
                prev_place = prev_act.place
                curr_place = a.place
                if prev_place and curr_place and prev_place.latitude and curr_place.latitude:
                    dist = haversine_distance_km(prev_place.latitude, prev_place.longitude, curr_place.latitude, curr_place.longitude)
                    is_intercity = (
                        meta.get("activity_type") == "transit"
                        or "transfer" in title_lower
                        or "transfer" in prev_act.title.lower()
                    )
                    if not is_intercity:
                        assert dist <= 45.0, f"Unrealistic within-day transit {dist:.1f} km between '{prev_act.title}' and '{a.title}' on Day {d.day_number}"

            if meta.get("activity_type") == "transit" or "transfer" in title_lower:
                intercity_transfers_found += 1
                assert a.duration_minutes >= 60, f"Intercity transfer '{a.title}' must have realistic duration (>= 1 hr)"
                print(f"      🚌 Explicit Intercity Transfer verified: {a.title} ({a.duration_minutes} mins)")

            # Criterion 5: Truthful Lake Titicaca Copacabana beach adaptation
            if "copacabana" in title_lower and ("beach" in title_lower or "titicaca" in title_lower):
                lake_titicaca_found = True

            # Criterion 6 & 7: Meal Semantics & Vegetarian Dietary Accuracy
            if meta.get("activity_type") == "meal" or "restaurant" in (a.place.category if a.place else "").lower() or "cafe" in (a.place.category if a.place else "").lower():
                vegetarian_meals_checked += 1
                # Must not be labeled Free Entry
                meal_cost = meta.get("meal_cost") or a.ticket_price
                assert meal_cost is not None, f"Dining activity '{a.title}' must have estimated meal cost"
                # Check vegetarian dish description
                sig_dish = (meta.get("meal_details") or {}).get("signature_dish") or meta.get("signature_dish") or ""
                dish_text = f"{a.title.lower()} {a.description.lower()} {sig_dish.lower()}"
                for meat in FORBIDDEN_MEAT_KEYWORDS:
                    assert meat not in dish_text, f"Vegetarian meal violation: found '{meat}' in dining activity '{a.title}'"
                print(f"      🌱 Verified Vegetarian Meal: {a.title} | Dish: '{sig_dish}' | Meal Cost: {meal_cost}")

            # Criterion 8: Sunset Timing
            if "sunset" in title_lower or "sunset" in a.description.lower():
                sunset_activities_checked += 1
                st_parts = a.start_time.split(":")
                st_mins = int(st_parts[0]) * 60 + int(st_parts[1])
                assert st_mins >= 17 * 60 + 15, f"Sunset activity '{a.title}' scheduled prematurely at {a.start_time} (must be >= 17:15)"
                print(f"      🌆 Sunset Activity Timing verified: {a.title} at {a.start_time} (Local sunset ~18:35)")

            # Criterion 10: Provenance attached
            prov = meta.get("provenance")
            assert prov is not None, f"Activity '{a.title}' must have provenance metadata"
            assert prov.get("source") is not None, f"Activity '{a.title}' provenance missing source"

            prev_act = a

    print(f"\nAudit Summary:")
    print(f"  Total Activities: {total_activities_count}")
    print(f"  Explicit Intercity Transfers: {intercity_transfers_found}")
    print(f"  Vegetarian Meals Audited: {vegetarian_meals_checked}")
    print(f"  Sunset Activities Audited: {sunset_activities_checked}")
    print(f"  Lake Titicaca Beach Found: {lake_titicaca_found}")

    assert total_activities_count >= 15, "Expected at least 15 activities across 5 days"
    assert intercity_transfers_found >= 2, "Expected at least 2 explicit intercity transfers (La Paz -> Copacabana and return)"
    assert vegetarian_meals_checked >= 4, "Expected at least 4 dining stops"
    assert sunset_activities_checked >= 1, "Expected at least 1 sunset activity"
    assert lake_titicaca_found, "Bolivia Beaches request must include Copacabana Lake Titicaca beach"

    # 8. Verify Today's Itinerary for Upcoming Trip
    print("\n" + "=" * 80)
    print("📅 Step 6: Verifying Upcoming Trip Dates in get_today_itinerary")
    print("=" * 80)

    today_itinerary = get_today_itinerary(trip.id, db, user_id=user.id)
    print(f"  Trip Status: {today_itinerary['trip_status']}")
    print(f"  Is Upcoming: {today_itinerary['is_upcoming_trip']}")
    print(f"  Reported Date ISO: {today_itinerary['date']}")
    print(f"  Reported Date Formatted: {today_itinerary['date_formatted']}")
    print(f"  Day Title: {today_itinerary['day_title']}")

    assert today_itinerary["date"] == "2026-11-06", f"Expected date '2026-11-06', got '{today_itinerary['date']}'"
    assert "06 November 2026" in today_itinerary["date_formatted"]
    print("✅ Step 6 PASSED: Upcoming trip correctly displays Day 1 date (06 November 2026)!")

    # 9. Verify enrich_trip_response (Non-Circular Budget Feasibility & Provenance)
    print("\n" + "=" * 80)
    print("📋 Step 7: Verifying Enriched Trip Response (Bottom-Up Budget & Serialization)")
    print("=" * 80)

    enriched = enrich_trip_response(trip, db)
    bp = enriched.get("budget_plan")
    assert bp is not None, "Budget plan must be present"

    rem_surplus = bp.get("remaining_budget", 0.0)
    min_c = bp["uncertainty_range"]["min_cost"]
    max_c = bp["uncertainty_range"]["max_cost"]
    print(f"  User Budget: ₹{bp['total_user_budget']:,.2f}")
    print(f"  Estimated Total Trip Cost: ₹{bp['total_estimated_trip_cost']:,.2f}")
    print(f"  Remaining Surplus Buffer: ₹{rem_surplus:,.2f} ({bp['surplus_buffer_percentage']}%)")
    print(f"  Uncertainty Range: ₹{min_c:,.2f} – ₹{max_c:,.2f}")
    print(f"  Cost Provenance: {bp['cost_provenance']}")
    print(f"  Feasible: {bp['is_feasible']}")

    # Criterion 9: Non-circular budget feasibility
    assert bp["total_user_budget"] == 150000.0, "User budget should be exactly ₹150,000"
    assert bp["total_estimated_trip_cost"] != bp["total_user_budget"], "Estimated cost must be calculated bottom-up, NOT circularly set equal to user budget!"
    assert rem_surplus > 0, "Remaining surplus buffer must be positive and visible"
    assert bp["is_feasible"] == True, "Trip must be within budget"
    assert bp["cost_provenance"] is not None, "Cost provenance must be stated"

    # Verify Days Serialization
    days_serialized = enriched["itinerary_days"]
    assert len(days_serialized) == 5
    for sd in days_serialized:
        print(f"  Serialized Day {sd['day_number']}: Base={sd.get('base_city')} | Overnight={sd.get('overnight_stay')}")
        assert sd.get("base_city") is not None, f"Day {sd['day_number']} missing base_city"
        assert sd.get("overnight_stay") is not None, f"Day {sd['day_number']} missing overnight_stay"

    print("\n" + "=" * 80)
    print("🎉 ALL 11 ITINERARY QUALITY & FEASIBILITY AUDIT CRITERIA PASSED FLAWLESSLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
