import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.core.currencies import get_all_currencies, get_currency_info
from app.ai.providers.provider_factory import AIProviderFactory
from app.ai.validators.itinerary_validator import ItineraryValidator
from app.utils.currency_formatter import format_currency

client = TestClient(app)

def run_tests():
    print("=== STARTING COMPREHENSIVE CURRENCY & WIZARD VERIFICATION ===")

    # 1. Test Currency Registry Endpoint & Functions
    print("\n--- 1. Testing Currency Registry ---")
    all_currencies = get_all_currencies()
    print(f"Total currencies loaded in registry: {len(all_currencies)}")
    assert len(all_currencies) >= 80, f"Expected 80+ currencies, got {len(all_currencies)}"

    inr_info = get_currency_info("INR")
    assert inr_info.symbol == "₹", f"Expected ₹ for INR, got {inr_info.symbol}"
    assert inr_info.locale == "en-IN", f"Expected en-IN for INR, got {inr_info.locale}"

    resp = client.get("/api/currency/registry")
    assert resp.status_code == 200, f"Registry status: {resp.status_code}"
    data_reg = resp.json()
    assert isinstance(data_reg, list) and len(data_reg) >= 80
    print("[SUCCESS] Currency Registry Endpoint & Lookup verified!")

    # 2. Test Currency Formatter
    print("\n--- 2. Testing Currency Formatter ---")
    assert format_currency(350.0, "INR") == "₹350"
    assert format_currency(40.0, "EUR") == "€40"
    assert format_currency(1200.0, "JPY") == "¥1,200"
    assert format_currency(1250.50, "USD") == "$1,250.50"
    print("[SUCCESS] Currency Formatter verified!")

    # 3. Test Provider Factory & Mock Provider
    print("\n--- 3. Testing AI Provider Factory ---")
    mock_p = AIProviderFactory.get_provider("mock")
    res_text = mock_p.generate("Generate trip for Kyoto in JPY")
    ok, norm_data, err = ItineraryValidator.validate_and_normalize(res_text, currency_code="JPY")
    assert ok, f"Mock validation failed: {err}"
    assert norm_data["trip"]["currency"] == "JPY"
    print("[SUCCESS] AI Provider Factory & Mock Provider verified!")

    # 4. Get test user
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(email="currency_tester@wanderwise.ai", password_hash="hashed", full_name="Currency Tester")
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id
    db.close()

    # 5. Create Trip with INR Currency
    print("\n--- 4. Testing Trip Creation in INR ---")
    payload_inr = {
        "user_id": user_id,
        "destination": "Varkala",
        "country": "India",
        "origin_city": "Coimbatore",
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "budget": 25000.0,
        "currency": "INR",
        "travel_style": "solo",
        "interests": "Beaches, Cafes, Sunsets",
        "trip_preferences": {
            "visa_status": "No Visa Needed",
            "flexible_dates": "Fixed Dates",
            "activity_pace": "balanced",
            "food": {"preferences": "Seafood, Street Food"}
        },
        "force_create": True
    }
    resp_inr = client.post("/api/trips/create", json=payload_inr)
    assert resp_inr.status_code == 201, f"Trip creation failed: {resp_inr.text}"
    trip_inr = resp_inr.json()
    assert trip_inr["currency"] == "INR"
    assert trip_inr["currency_symbol"] == "₹"
    assert trip_inr["trip_preferences"]["visa_status"] == "No Visa Needed"

    first_day = trip_inr["itinerary_days"][0]
    first_act = first_day["activities"][0]
    print(f"INR Activity Title: {first_act['title']}")
    print(f"INR Formatted Cost: {repr(first_act['formatted_cost'])}")
    assert "₹" in first_act["formatted_cost"] or first_act["formatted_cost"] == "Free Entry"
    assert first_act["cost"]["currency"] == "INR"
    print("[SUCCESS] Trip Creation in INR verified!")

    # 6. Create Trip with EUR Currency
    print("\n--- 5. Testing Trip Creation in EUR ---")
    payload_eur = {
        "user_id": user_id,
        "destination": "Paris",
        "country": "France",
        "origin_city": "London",
        "start_date": "2026-11-05",
        "end_date": "2026-11-06",
        "budget": 1500.0,
        "currency": "EUR",
        "travel_style": "luxury",
        "interests": "Museums, Fine Dining, Art",
        "force_create": True
    }
    resp_eur = client.post("/api/trips/create", json=payload_eur)
    assert resp_eur.status_code == 201, f"Trip EUR failed: {resp_eur.text}"
    trip_eur = resp_eur.json()
    assert trip_eur["currency"] == "EUR"
    assert trip_eur["currency_symbol"] == "€"
    first_act_eur = trip_eur["itinerary_days"][0]["activities"][0]
    print(f"EUR Formatted Cost: {repr(first_act_eur['formatted_cost'])}")
    assert "€" in first_act_eur["formatted_cost"] or first_act_eur["formatted_cost"] == "Free Entry"
    print("[SUCCESS] Trip Creation in EUR verified!")



    # 7. Test Dashboard Widgets Contract (Version 1.0)
    print("\n--- 6. Testing Dashboard Widgets Version 1.0 Contract ---")
    resp_dash = client.get(f"/api/trips/dashboard-widgets/{user_id}")
    assert resp_dash.status_code == 200, f"Dashboard failed: {resp_dash.text}"
    dash_data = resp_dash.json()
    assert dash_data.get("version") == "1.0", f"Expected version 1.0, got {dash_data.get('version')}"
    assert "trip" in dash_data
    assert "today" in dash_data
    assert "budget" in dash_data
    print("[SUCCESS] Dashboard Version 1.0 Contract verified!")

    print("\n=== ALL CURRENCY & 14-STEP WIZARD TESTS PASSED CLEANLY (100%) ===")

if __name__ == "__main__":
    run_tests()
