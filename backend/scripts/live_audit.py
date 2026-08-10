import os
import requests
import uuid
import sys
import json
import time

BASE_URL = "http://localhost:8000/api"

def get_unique_email():
    return f"audit_user_{uuid.uuid4().hex[:8]}@example.com"

results = []

def run_test(section, name, fn, expected_status=None):
    try:
        resp = fn()
        if expected_status:
            if resp.status_code == expected_status:
                results.append((section, name, "PASS", f"HTTP {resp.status_code}"))
            else:
                results.append((section, name, "FAIL", f"Expected HTTP {expected_status}, got {resp.status_code} - {resp.text[:100]}"))
        else:
            results.append((section, name, "PASS", "Executed without error"))
        return resp
    except Exception as e:
        results.append((section, name, "FAIL", f"Exception: {e}"))
        return None

def main():
    print("Starting Live API Verification...")

    # 1. Register / Login
    email_a = get_unique_email()
    email_b = get_unique_email()
    
    # Registration
    run_test("AUTH", "Register User A", lambda: requests.post(f"{BASE_URL}/auth/register", json={"email": email_a, "password": "password123", "name": "Audit User A"}), 200)
    run_test("AUTH", "Register User B", lambda: requests.post(f"{BASE_URL}/auth/register", json={"email": email_b, "password": "password123", "name": "Audit User B"}), 200)
    
    # Login
    resp_a = run_test("AUTH", "Login User A", lambda: requests.post(f"{BASE_URL}/auth/login", json={"email": email_a, "password": "password123"}), 200)
    token_a = resp_a.json()["access_token"] if resp_a and resp_a.status_code == 200 else None
    
    resp_b = requests.post(f"{BASE_URL}/auth/login", json={"email": email_b, "password": "password123"})
    token_b = resp_b.json()["access_token"] if resp_b and resp_b.status_code == 200 else None

    if not token_a or not token_b:
        print("Failed to authenticate. Aborting.")
        return

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Protected endpoint without token
    run_test("AUTH", "Protected endpoint (trips) without token", lambda: requests.get(f"{BASE_URL}/trips"), 401)
    run_test("AUTH", "Protected endpoint (documents) without token", lambda: requests.get(f"{BASE_URL}/documents/"), 401)

    # 3. Protected endpoint with valid token
    run_test("AUTH", "Protected endpoint (trips) with valid token", lambda: requests.get(f"{BASE_URL}/trips", headers=headers_a), 200)

    # 4. Invalid weather city
    run_test("WEATHER", "Invalid weather city (404/503)", lambda: requests.get(f"{BASE_URL}/weather/NotARealCity123"), 404)

    # 5. Valid weather city
    run_test("WEATHER", "Valid weather city (200)", lambda: requests.get(f"{BASE_URL}/weather/London"), 200)

    # 6. Currency conversion
    run_test("CURRENCY", "Currency conversion contract", lambda: requests.get(f"{BASE_URL}/currency/convert?from_currency=USD&to_currency=EUR&amount=100"), 200)

    # 7. AI Itinerary Generation
    # Depending on AI keys, this might be 503 or 200. The prompt says "A feature is COMPLETE only if successful generation works with a valid configuration."
    itinerary_resp = run_test("AI ITINERARY", "Generate Itinerary", lambda: requests.post(f"{BASE_URL}/trips/create", headers=headers_a, json={"destination": "Paris", "start_date": "2026-08-01", "end_date": "2026-08-03", "budget": 1000}), 201)
    
    # 8. Recommendations
    run_test("RECOMMENDATIONS", "Get Personalized Recommendations", lambda: requests.get(f"{BASE_URL}/recommendations/personalized", headers=headers_a), 200)

    # 9. Transit
    run_test("TRANSIT", "Route between cities", lambda: requests.get(f"{BASE_URL}/transit/route?origin_lat=51.5&origin_lon=-0.1&dest_lat=48.8&dest_lon=2.3"), 200)

    # 10. Budget
    expense_resp = run_test("BUDGET", "Create Expense", lambda: requests.post(f"{BASE_URL}/expenses", headers=headers_a, json={"trip_id": 9999, "amount": 100, "currency": "USD", "category": "food", "description": "Dinner", "date": "2026-01-01"}))
    if expense_resp:
        if expense_resp.status_code in [200, 404, 400]:
            results.append(("BUDGET", "Expense creation handled", "PASS", f"HTTP {expense_resp.status_code}"))
        else:
            results.append(("BUDGET", "Expense creation handled", "FAIL", f"HTTP {expense_resp.status_code}"))

    # 11. Packing
    run_test("PACKING", "Generate Packing List", lambda: requests.post(f"{BASE_URL}/packing/generate", json={"destination": "London", "duration": 3, "travel_type": "leisure"}), 200)

    # 12. Emergency
    run_test("EMERGENCY", "Get Emergency Numbers", lambda: requests.get(f"{BASE_URL}/safety/emergency?country=UK"), 200)

    # 13. Journal
    journal_resp = run_test("JOURNAL", "Create Journal Entry", lambda: requests.post(f"{BASE_URL}/journal", headers=headers_a, json={"trip_id": None, "title": "Audit Trip", "content": "Hello", "location": "London"}), 200)
    if journal_resp and journal_resp.status_code == 200:
        entry_id = journal_resp.json().get("id")
        if entry_id:
            # Try to read with user B
            run_test("JOURNAL", "Cross-user Journal Access Denied", lambda: requests.get(f"{BASE_URL}/journal/entries/{entry_id}", headers=headers_b), 404)

    # 14. Documents Vault
    # Requires a file upload
    import io
    files = {'file': ('test.txt', io.BytesIO(b"Hello Document Vault"), 'text/plain')}
    doc_resp = run_test("DOCUMENTS", "Upload Document", lambda: requests.post(f"{BASE_URL}/documents", headers=headers_a, files=files, data={"trip_id": 9999, "category": "other"}), 200)

    # 15. Checklist
    chk_resp = run_test("CHECKLIST", "Create Checklist Item", lambda: requests.post(f"{BASE_URL}/safety/checklist", headers=headers_a, json={"item_text": "Passport", "user_id": 1}), 200)
    if chk_resp and chk_resp.status_code == 200:
        item_id = chk_resp.json().get("id")
        run_test("CHECKLIST", "Cross-user Checklist Access Denied", lambda: requests.delete(f"{BASE_URL}/safety/checklist/{item_id}", headers=headers_b), 404)

    # Dashboard 
    run_test("DASHBOARD", "Dashboard valid response", lambda: requests.get(f"{BASE_URL}/safety/dashboard?destination=London"), 200)


    print("\n--- RESULTS ---")
    for r in results:
        print(f"[{r[0]}] {r[1]} - {r[2]}: {r[3]}")

if __name__ == "__main__":
    main()
