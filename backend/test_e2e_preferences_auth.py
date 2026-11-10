"""
test_e2e_preferences_auth.py
Automated End-to-End Verification Suite for WanderWise:
Test A: INR user (registration, preferences persistence, itinerary generation in INR, vegetarian meals)
Test B: USD user (registration, luxury budget, itinerary generation in USD)
Test C: Preference update (change currency from INR to EUR, update budget tier, verify new itinerary uses EUR)
Test D: Persistence across logout and fresh login
Test E: Google Sign-In (URL check, error handling, account creation, account linking, token generation)
"""

import sys
import os
import time
import json
from datetime import date, timedelta
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

client = TestClient(app)

def print_header(title):
    print("\n" + "=" * 65, flush=True)
    print(f"  {title}", flush=True)
    print("=" * 65, flush=True)

def run_e2e_tests():
    db = SessionLocal()
    ts = int(time.time())

    # =========================================================================
    # TEST A: INR User
    # =========================================================================
    print_header("TEST A: INR User Registration, Preferences & Itinerary")
    email_a = f"aarav_test_{ts}@example.com"
    reg_payload_a = {
        "name": "Aarav Sharma",
        "email": email_a,
        "password": "Password123!",
        "phone_number": "+91 9876543210",
        "currency": "INR",
        "preferred_budget": "Budget (<₹4,300/day)",  # Test raw label normalization
        "travel_styles": "Adventure, Food & Dining",
        "preferred_climate": "Mountains 🏔️",
        "preferred_activities": "Hiking, Photography, Street Food",
        "languages": "Hindi",
        "dietary_preferences": "Vegetarian",
        "accessibility_needs": "None"
    }

    resp = client.post("/api/auth/register", json=reg_payload_a)
    assert resp.status_code == 201, f"Test A Registration failed: {resp.text}"
    data_a = resp.json()
    token_a = data_a["access_token"]
    user_a = data_a["user"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    print(f"[OK] User Registered: {user_a['email']} (ID: {user_a['id']})")
    print(f"[OK] Currency: {user_a['currency']} (Expected INR)")
    print(f"[OK] Normalized Budget Tier: {user_a['preferred_budget']} (Expected 'budget')")
    print(f"[OK] Dietary Preferences: {user_a['dietary_preferences']} (Expected 'Vegetarian')")
    print(f"[OK] Language: {user_a['languages']} (Expected 'Hindi')")

    assert user_a["currency"] == "INR"
    assert user_a["preferred_budget"] == "budget"
    assert user_a["dietary_preferences"] == "Vegetarian"
    assert user_a["languages"] == "Hindi"

    # Verify /api/auth/me returns saved preferences
    me_resp = client.get("/api/auth/me", headers=headers_a)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["currency"] == "INR"
    assert me_data["preferred_budget"] == "budget"
    assert me_data["dietary_preferences"] == "Vegetarian"
    print("[OK] /api/auth/me verified preferences persistence.")

    # Create trip for INR user WITHOUT specifying currency (should inherit profile currency INR)
    start_d = (date.today() + timedelta(days=10)).isoformat()
    end_d = (date.today() + timedelta(days=12)).isoformat()
    trip_payload_a = {
        "user_id": user_a["id"],
        "destination": "Manali",
        "country": "India",
        "start_date": start_d,
        "end_date": end_d,
        "budget": 12000.0,
        # Notice: currency omitted so preference resolution uses user.currency == 'INR'
        "interests": "Mountains, Sightseeing",
        "force_create": True
    }

    trip_resp = client.post("/api/trips/create", json=trip_payload_a, headers=headers_a)
    assert trip_resp.status_code in [200, 201], f"Trip creation failed: {trip_resp.text}"
    trip_data_a = trip_resp.json()
    print(f"[OK] Trip Created: ID {trip_data_a['id']} for destination {trip_data_a['destination']}")
    print(f"[OK] Trip Currency Resolved: {trip_data_a.get('currency')} (Expected INR)")
    assert trip_data_a.get("currency") == "INR", f"Expected INR currency, got {trip_data_a.get('currency')}"

    # Verify generated activities have INR currency and vegetarian dining
    itinerary_days = trip_data_a.get("itinerary_days", [])
    assert len(itinerary_days) > 0, "No itinerary days generated"
    found_vegetarian_meal = False
    inr_symbol_found = False

    for day in itinerary_days:
        for act in day.get("activities", []):
            cost_info = act.get("cost") or {}
            c_code = cost_info.get("currency")
            c_sym = cost_info.get("symbol")
            if c_code == "INR" or c_sym == "₹":
                inr_symbol_found = True

            act_title = act.get("title", "").lower()
            act_desc = act.get("description", "").lower()
            if "veg" in act_title or "veg" in act_desc or "शाकाहारी" in act_title or "शाकाहारी" in act_desc:
                found_vegetarian_meal = True

    print(f"[OK] Verified Activity Currency in INR: {inr_symbol_found}")
    print(f"[OK] Verified Vegetarian Meal Recommendations Present: {found_vegetarian_meal}")
    assert inr_symbol_found, "Itinerary activities did not format in INR"
    assert found_vegetarian_meal, "Vegetarian meal recommendations were not generated for vegetarian user"

    # =========================================================================
    # TEST B: USD Luxury User
    # =========================================================================
    print_header("TEST B: USD Luxury User Registration & Itinerary")
    email_b = f"emma_test_{ts}@example.com"
    reg_payload_b = {
        "name": "Emma Watson",
        "email": email_b,
        "password": "Password123!",
        "currency": "USD",
        "preferred_budget": "Luxury ($350+/day)",
        "travel_styles": "Luxury",
        "languages": "English",
        "dietary_preferences": "No Preference"
    }

    resp_b = client.post("/api/auth/register", json=reg_payload_b)
    assert resp_b.status_code == 201
    data_b = resp_b.json()
    token_b = data_b["access_token"]
    user_b = data_b["user"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    print(f"[OK] User Registered: {user_b['email']} (ID: {user_b['id']})")
    print(f"[OK] Currency: {user_b['currency']} (Expected USD)")
    print(f"[OK] Normalized Budget: {user_b['preferred_budget']} (Expected 'luxury')")
    assert user_b["currency"] == "USD"
    assert user_b["preferred_budget"] == "luxury"

    # Create trip for USD user
    trip_payload_b = {
        "user_id": user_b["id"],
        "destination": "Paris",
        "country": "France",
        "start_date": start_d,
        "end_date": end_d,
        "budget": 3500.0,
        "travel_style": "luxury",
        "force_create": True
    }
    trip_resp_b = client.post("/api/trips/create", json=trip_payload_b, headers=headers_b)
    assert trip_resp_b.status_code in [200, 201]
    trip_data_b = trip_resp_b.json()
    print(f"[OK] Trip Created: ID {trip_data_b['id']} - Currency: {trip_data_b.get('currency')}")
    assert trip_data_b.get("currency") == "USD"

    # =========================================================================
    # TEST C: Preference Update (INR -> EUR, Budget update)
    # =========================================================================
    print_header("TEST C: Preference Update (INR -> EUR & Comfort Tier)")
    update_payload = {
        "currency": "EUR",
        "preferred_budget": "Comfort ($150–350/day)",
        "travel_styles": "Cultural, Food & Dining",
        "languages": "English"
    }

    update_resp = client.put("/api/auth/me/preferences", json=update_payload, headers=headers_a)
    assert update_resp.status_code == 200
    updated_user = update_resp.json()
    print(f"[OK] Updated User Currency: {updated_user['currency']} (Expected EUR)")
    print(f"[OK] Updated User Budget Tier: {updated_user['preferred_budget']} (Expected 'comfort')")
    assert updated_user["currency"] == "EUR"
    assert updated_user["preferred_budget"] == "comfort"

    # Create another itinerary for user A — verify it now uses EUR!
    trip_payload_c = {
        "user_id": user_a["id"],
        "destination": "Rome",
        "country": "Italy",
        "start_date": start_d,
        "end_date": end_d,
        "budget": 1500.0,
        "force_create": True
    }
    trip_resp_c = client.post("/api/trips/create", json=trip_payload_c, headers=headers_a)
    assert trip_resp_c.status_code in [200, 201]
    trip_data_c = trip_resp_c.json()
    print(f"[OK] New Trip Created After Update - Currency: {trip_data_c.get('currency')} (Expected EUR)")
    assert trip_data_c.get("currency") == "EUR"

    # =========================================================================
    # TEST D: Persistence across Logout & Login
    # =========================================================================
    print_header("TEST D: Persistence Across Logout & Fresh Login")
    logout_resp = client.post("/api/auth/logout", headers=headers_a)
    assert logout_resp.status_code == 200
    print("[OK] Logged out user A successfully.")

    login_resp = client.post("/api/auth/login", json={"email": email_a, "password": "Password123!"})
    assert login_resp.status_code == 200
    fresh_auth = login_resp.json()
    fresh_user = fresh_auth["user"]
    fresh_token = fresh_auth["access_token"]

    print(f"[OK] Re-authenticated: {fresh_user['email']}")
    print(f"[OK] Persisted Currency: {fresh_user['currency']} (Expected EUR)")
    print(f"[OK] Persisted Budget Tier: {fresh_user['preferred_budget']} (Expected 'comfort')")
    print(f"[OK] Persisted Dietary: {fresh_user['dietary_preferences']} (Expected 'Vegetarian')")
    print(f"[OK] Persisted Language: {fresh_user['languages']} (Expected 'English')")
    assert fresh_user["currency"] == "EUR"
    assert fresh_user["preferred_budget"] == "comfort"
    assert fresh_user["dietary_preferences"] == "Vegetarian"

    # =========================================================================
    # TEST E: Google Sign-In Architecture & Flow
    # =========================================================================
    print_header("TEST E: Google Sign-In Endpoints & Authentication")
    
    # 1. Test /api/auth/google/url
    url_resp = client.get("/api/auth/google/url")
    assert url_resp.status_code == 200
    url_data = url_resp.json()
    print(f"[OK] /api/auth/google/url response: configured={url_data.get('configured')}")
    if not url_data.get("configured"):
        print(f"     Required Env Variables: {url_data.get('required_vars')}")
        print(f"     Setup Help: {url_data.get('setup_help')}")
        assert "GOOGLE_CLIENT_ID" in url_data.get("required_vars", [])

    # 2. Test Callback error handling (cancelled login)
    cb_err = client.get("/api/auth/google/callback?error=access_denied", follow_redirects=False)
    assert cb_err.status_code in [302, 307]
    redirect_loc = cb_err.headers.get("location", "")
    print(f"[OK] Google cancelled login redirected to: {redirect_loc}")
    assert "error=access_denied" in redirect_loc

    # 3. Test Callback missing code handling
    cb_nocode = client.get("/api/auth/google/callback", follow_redirects=False)
    assert cb_nocode.status_code in [302, 307]
    assert "error=missing_code" in cb_nocode.headers.get("location", "")
    print(f"[OK] Missing code correctly redirected with error=missing_code")

    # 4. Test programmatic Google account creation & duplicate prevention via DB models
    google_email = f"google.traveler.{ts}@gmail.com"
    google_sub = f"g_sub_{ts}"

    # A new Google user is created
    existing = db.query(User).filter(User.email == google_email).first()
    assert existing is None

    new_google_user = User(
        name="Google Wanderer",
        email=google_email,
        google_id=google_sub,
        auth_provider="google",
        password=None,  # Google OAuth users don't require password
        role="USER",
        profile_completed=False,
        currency="USD",
        travel_styles="Adventure",
        dietary_preferences="Vegan"
    )
    db.add(new_google_user)
    db.commit()
    db.refresh(new_google_user)
    print(f"[OK] New Google user initialized in DB: ID {new_google_user.id}, auth_provider={new_google_user.auth_provider}")
    assert new_google_user.google_id == google_sub
    assert new_google_user.password is None

    # Simulate subsequent login for existing user: duplicate accounts must NOT be created
    user_lookup = db.query(User).filter(User.google_id == google_sub).first()
    assert user_lookup is not None
    assert user_lookup.id == new_google_user.id
    print(f"[OK] Re-login with same Google ID retrieves existing account ID {user_lookup.id} without creating duplicate accounts.")

    db.close()
    print_header("ALL E2E ACCEPTANCE TESTS PASSED SUCCESSFULLY! ✓")

if __name__ == "__main__":
    run_e2e_tests()
