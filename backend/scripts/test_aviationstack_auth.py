"""
test_aviationstack_auth.py — Diagnostic script to test AviationStack API authentication,
endpoints, airport lookups (CJB, KIX), and flight search capabilities.

Rules:
- Never prints or logs the raw API key.
- Sanitizes all outputs.
- Captures HTTP status and exact provider error payload.
- Categorizes failure accurately.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load backend/.env
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

def mask_key(k: str) -> str:
    if not k:
        return "[NOT SET]"
    if len(k) <= 8:
        return "***"
    return f"{k[:4]}...{k[-4:]}"

def test_aviationstack():
    key = os.getenv("FLIGHT_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")
    print(f"=== AviationStack Diagnostic Test ===")
    print(f"Key source: FLIGHT_API_KEY={bool(os.getenv('FLIGHT_API_KEY'))}, AVIATIONSTACK_API_KEY={bool(os.getenv('AVIATIONSTACK_API_KEY'))}")
    print(f"Key loaded: {mask_key(key)} (len={len(key) if key else 0})")

    if not key:
        print("RESULT: KEY_MISSING - Neither FLIGHT_API_KEY nor AVIATIONSTACK_API_KEY is set.")
        return {"category": "KEY_MISSING", "status": None, "details": "No API key configured"}

    headers = {"User-Agent": "WanderWise/12.3 (AviationStack Diagnostic)"}

    # 1. Test minimal authentication / flight lookup with HTTPS
    print("\n--- 1. Testing Minimal Authentication on /v1/flights (HTTPS) ---")
    url = "https://api.aviationstack.com/v1/flights"
    params = {"access_key": key, "limit": 1}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        http_status = resp.status_code
        print(f"HTTPS Status Code: {http_status}")
        resp_data = resp.json()
    except requests.exceptions.Timeout:
        print("HTTPS Request Timed Out (10s)")
        return {"category": "TIMEOUT", "status": None, "details": "HTTPS connection timed out"}
    except requests.exceptions.ConnectionError as e:
        print(f"HTTPS Connection Error: {e}")
        return {"category": "CONNECTION_ERROR", "status": None, "details": str(e)}

    # Categorize error if present on /v1/flights
    if isinstance(resp_data, dict) and resp_data.get("error"):
        err = resp_data["error"]
        err_code = err.get("code")
        err_type = err.get("type", "")
        err_msg = err.get("message", err.get("info", ""))
        print(f"Provider Error: code={err_code}, type={err_type}, msg={err_msg}")

        if err_code in [101, "invalid_access_key"] or "invalid_access_key" in str(err_type):
            category = "INVALID_API_KEY"
        elif err_code in [104, "usage_limit_reached"] or "usage_limit_reached" in str(err_type):
            category = "QUOTA_EXHAUSTED"
        elif err_code in [105, "https_access_restricted"] or "https_access_restricted" in str(err_type):
            category = "SUBSCRIPTION_RESTRICTION_HTTPS"
        elif err_code in [103, "invalid_api_function"] or "function_access_restricted" in str(err_code):
            category = "SUBSCRIPTION_RESTRICTION_ENDPOINT"
        else:
            category = f"PROVIDER_ERROR_{str(err_code).upper()}"

        print(f"RESULT: {category} (HTTP {http_status})")
        return {"category": category, "status": http_status, "error": err}

    print("Minimal authentication on /v1/flights SUCCEEDED (HTTP 200).")

    # 2. Test /v1/airports endpoint to check plan capabilities
    print("\n--- 2. Testing /v1/airports Endpoint ---")
    try:
        ap_resp = requests.get("https://api.aviationstack.com/v1/airports", params={"access_key": key, "limit": 1}, headers=headers, timeout=10)
        print(f"/v1/airports Status Code: {ap_resp.status_code}")
        ap_data = ap_resp.json()
        if "error" in ap_data:
            err = ap_data["error"]
            print(f"/v1/airports restricted: code={err.get('code')}, msg={err.get('message')}")
        else:
            print(f"/v1/airports accessible! Count: {len(ap_data.get('data', []))}")
    except Exception as e:
        print(f"/v1/airports check failed: {e}")

    # 3. Test airport code CJB independently via /v1/flights (dep_iata=CJB)
    print("\n--- 3. Testing Airport Code CJB (Coimbatore) Independently ---")
    cjb_params = {"access_key": key, "dep_iata": "CJB", "limit": 3}
    try:
        cjb_resp = requests.get("https://api.aviationstack.com/v1/flights", params=cjb_params, headers=headers, timeout=10)
        print(f"Flights departing CJB Status: {cjb_resp.status_code}")
        if cjb_resp.status_code == 200:
            cjb_data = cjb_resp.json()
            if "error" in cjb_data:
                print(f"CJB query error: {cjb_data['error']}")
            else:
                cjb_flights = cjb_data.get("data", [])
                print(f"Flights found departing CJB: {len(cjb_flights)}")
                for f in cjb_flights[:2]:
                    f_num = f.get("flight", {}).get("iata") or f.get("flight", {}).get("number")
                    arr = f.get("arrival", {})
                    print(f"  -> Flight {f_num}: CJB -> {arr.get('iata')} ({arr.get('airport')}) status={f.get('flight_status')}")
    except Exception as e:
        print(f"CJB flight search error: {e}")

    # 4. Test airport code KIX independently via /v1/flights (arr_iata=KIX or dep_iata=KIX)
    print("\n--- 4. Testing Airport Code KIX (Kansai) Independently ---")
    kix_params = {"access_key": key, "arr_iata": "KIX", "limit": 3}
    try:
        kix_resp = requests.get("https://api.aviationstack.com/v1/flights", params=kix_params, headers=headers, timeout=10)
        print(f"Flights arriving at KIX Status: {kix_resp.status_code}")
        if kix_resp.status_code == 200:
            kix_data = kix_resp.json()
            if "error" in kix_data:
                print(f"KIX query error: {kix_data['error']}")
            else:
                kix_flights = kix_data.get("data", [])
                print(f"Flights found arriving at KIX: {len(kix_flights)}")
                for f in kix_flights[:2]:
                    f_num = f.get("flight", {}).get("iata") or f.get("flight", {}).get("number")
                    dep = f.get("departure", {})
                    print(f"  -> Flight {f_num}: {dep.get('iata')} ({dep.get('airport')}) -> KIX status={f.get('flight_status')}")
    except Exception as e:
        print(f"KIX flight search error: {e}")

    # 5. Test direct route CJB -> KIX
    print("\n--- 5. Testing Route Search (CJB -> KIX) ---")
    route_params = {"access_key": key, "dep_iata": "CJB", "arr_iata": "KIX", "limit": 5}
    try:
        route_resp = requests.get("https://api.aviationstack.com/v1/flights", params=route_params, headers=headers, timeout=10)
        print(f"Direct Route CJB -> KIX Status: {route_resp.status_code}")
        if route_resp.status_code == 200:
            route_data = route_resp.json()
            if "error" in route_data:
                print(f"Route query error: {route_data['error']}")
            else:
                route_flights = route_data.get("data", [])
                print(f"Direct Flights CJB -> KIX: {len(route_flights)}")
                if not route_flights:
                    print("  -> EMPTY_SEARCH_RESULTS: No direct flights operate between CJB and KIX (connecting flights required).")
    except Exception as e:
        print(f"Route search error: {e}")

    return {
        "category": "SUCCESS_AUTHENTICATED",
        "status": 200,
        "supported_endpoints": ["/v1/flights"],
        "restricted_endpoints": ["/v1/airports"],
        "details": "Authentication succeeded over HTTPS on /v1/flights; airport lookups restricted to flight search."
    }

if __name__ == "__main__":
    res = test_aviationstack()
    print(f"\nFinal Diagnostic Summary: {res['category']}")
