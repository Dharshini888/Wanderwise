import os
import requests
import uuid
import sys

BASE_URL = "http://localhost:8000/api"

def get_unique_email():
    return f"test_user_{uuid.uuid4().hex[:8]}@example.com"

# 1. Registration and Auth helpers
def register_user(email, password="password123"):
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "name": "Test User"
    })
    return resp

def login_user(email, password="password123"):
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    return resp.json()["access_token"]

def print_result(section, test_name, success, msg=""):
    status = "PASS" if success else "FAIL"
    print(f"[{section}] {status} | {test_name} {f'- {msg}' if msg else ''}")
    return success

all_passed = True

def run():
    global all_passed

    print("========================================")
    print("WANDERWISE PHASE 1 ACCEPTANCE TEST")
    print("========================================\n")

    # Setup Users
    email_a = get_unique_email()
    email_b = get_unique_email()

    register_user(email_a)
    register_user(email_b)

    token_a = login_user(email_a)
    token_b = login_user(email_b)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. AUTH / SECURITY TESTS
    resp = requests.get(f"{BASE_URL}/trips", headers={})
    p = print_result("AUTH", "Missing token returns 401", resp.status_code == 401)
    all_passed = all_passed and p

    # 2. CHECKLIST (Cross-user test)
    resp = requests.post(f"{BASE_URL}/safety/checklist", headers=headers_a, json={"item_text": "Passport"})
    if resp.status_code == 200:
        item_id = resp.json().get("id")
        # Try to delete with user B
        del_resp = requests.delete(f"{BASE_URL}/safety/checklist/{item_id}", headers=headers_b)
        # Should be 404 or 403
        p = print_result("SECURITY", "Cross-user delete prevention", del_resp.status_code in [403, 404])
        all_passed = all_passed and p
    else:
        print_result("CHECKLIST", "Create checklist item", False, f"Failed with {resp.status_code}")
        all_passed = False

    # 3. WEATHER
    resp = requests.get(f"{BASE_URL}/weather/DefinitelyNotARealCity123")
    p = print_result("WEATHER", "Invalid city returns 404/503", resp.status_code in [404, 503])
    all_passed = all_passed and p

    resp = requests.get(f"{BASE_URL}/weather/London")
    p = print_result("WEATHER", "Valid city returns 200", resp.status_code == 200)
    all_passed = all_passed and p
    if resp.status_code == 200:
        data = resp.json()
        p = print_result("WEATHER", "No fabricated fallback", data.get("current", {}).get("description") != "Estimated Weather")
        all_passed = all_passed and p

    # 4. CURRENCY
    resp = requests.get(f"{BASE_URL}/currency/convert?from_currency=USD&to_currency=EUR&amount=100")
    p = print_result("CURRENCY", "API contract from_currency", resp.status_code == 200)
    all_passed = all_passed and p

    # 5. PACKING
    resp = requests.post(f"{BASE_URL}/packing/generate", json={"destination": "", "duration": 0, "travel_type": ""})
    p = print_result("PACKING", "AI Failure returns 503/400 (Not 500)", resp.status_code in [503, 400, 422])
    all_passed = all_passed and p

    # 6. DASHBOARD
    resp = requests.get(f"{BASE_URL}/safety/dashboard?destination=London")
    p = print_result("DASHBOARD", "Valid Dashboard Response", resp.status_code == 200)
    all_passed = all_passed and p
    if resp.status_code == 200:
        data = resp.json()
        has_ai_risk = bool(data.get("ai_risk"))
        p = print_result("DASHBOARD", "No Phase 2 ai_risk", not has_ai_risk)
        all_passed = all_passed and p

    # 7. RECOMMENDATIONS
    resp = requests.get(f"{BASE_URL}/recommendations/personalized", headers=headers_a)
    p = print_result("RECOMMENDATIONS", "Phase 1 recommendations isolated", resp.status_code == 200)
    all_passed = all_passed and p

    # 8. EMERGENCY HUB
    resp = requests.get(f"{BASE_URL}/safety/emergency?country=UK")
    p = print_result("EMERGENCY", "Emergency lookup", resp.status_code == 200)
    all_passed = all_passed and p

    # 9. TRANSIT
    resp = requests.get(f"{BASE_URL}/transit/route?origin=London&destination=Paris")
    # Could be 200 or 503, just ensure not 500
    p = print_result("TRANSIT", "Transit routing", resp.status_code in [200, 503])
    all_passed = all_passed and p

    # 10. JOURNAL (CRUD)
    resp = requests.post(f"{BASE_URL}/journal/entries", headers=headers_a, json={
        "trip_id": None, "title": "Test Entry", "content": "Hello", "location": "London"
    })
    p = print_result("JOURNAL", "Create journal", resp.status_code == 200)
    all_passed = all_passed and p
    
    # 11. BUDGET PLANNER
    resp = requests.post(f"{BASE_URL}/expenses", headers=headers_a, json={
        "trip_id": 1, "amount": 100, "currency": "USD", "category": "food", "description": "Dinner", "date": "2026-01-01"
    })
    # Since trip doesn't exist, it might 404, or 400, but not 500
    p = print_result("BUDGET", "Expense creation isolated", resp.status_code in [200, 404, 400])
    all_passed = all_passed and p
    
    # 12. AI ITINERARY
    resp = requests.post(f"{BASE_URL}/trips/generate", headers=headers_a, json={
        "destination": "London", "duration": 3, "budget": 500, "travel_style": "leisure"
    })
    p = print_result("AI ITINERARY", "AI Itinerary Generation", resp.status_code in [200, 503])
    all_passed = all_passed and p

    print("\n========================================")
    print("FINAL RESULT")
    print("========================================")
    if all_passed:
        print("PHASE 1 STATUS: ACCEPTED")
        sys.exit(0)
    else:
        print("PHASE 1 STATUS: NOT ACCEPTED")
        sys.exit(1)

if __name__ == "__main__":
    run()
