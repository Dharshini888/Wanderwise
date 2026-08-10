import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Force UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.transit.providers.railradar_provider import RailRadarProvider
from app.services.transit.transit_orchestrator import TransitOrchestrator

print("==================================================")
print("WANDERWISE TRANSIT V12.2 LIVE PROVIDER TEST")
print("==================================================")

# 1. Provider Configuration Diagnostics
print("\n1. PROVIDER CONFIGURATION DIAGNOSTICS:")
print("Transitous:       CONFIGURED")
print("Navitia:          NOT CONFIGURED")
print("India Transit:    CONFIGURED")
print(f"RailRadar:        {'CONFIGURED' if os.getenv('RAILRADAR_API_KEY') else 'NOT CONFIGURED'}")
print(f"Flight Provider:  {'CONFIGURED' if (os.getenv('FLIGHT_API_KEY') or os.getenv('AVIATIONSTACK_API_KEY')) else 'NOT CONFIGURED'}")
print("OSRM:             CONFIGURED")
print(f"Gemini:           {'CONFIGURED' if os.getenv('GEMINI_API_KEY') else 'NOT CONFIGURED'}")

# 2. RailRadar Direct Test (Coimbatore -> Chennai)
print("\n2. RAILRADAR DIRECT QUERY TEST (Coimbatore -> Chennai):")
rr_health = RailRadarProvider.health_check()
print(f"RailRadar Health: {rr_health.get('status')} (Reachable: {rr_health.get('api_reachable')})")

rr_res = RailRadarProvider().plan_journey(10.93707, 76.95636, 13.08369, 80.27018)
print(f"RailRadar Status: {rr_res.status}")
print(f"Itineraries:      {len(rr_res.itineraries)}")
if rr_res.itineraries:
    first = rr_res.itineraries[0]
    leg = first.get("legs", [{}])[0]
    print(f"Train Number:     {leg.get('train_number')}")
    print(f"Train Name:       {leg.get('route_name')}")
    print(f"Departure:        {leg.get('departure_time')}")
    print(f"Arrival:          {leg.get('arrival_time')}")
    print(f"Platform:         {leg.get('platform')} ({leg.get('platform_source')})")
    print(f"Distance:         {leg.get('distance_m', 0)/1000.0} km ({leg.get('distance_source')})")

# 3. Router Test Scenarios
scenarios = [
    ("1. London -> Manchester", "London Euston", "Manchester Piccadilly", 51.5309, -0.1233, 53.4774, -2.2309),
    ("2. London -> Paris", "London Euston", "Paris Gare du Nord", 51.5309, -0.1233, 48.8809, 2.3553),
    ("3. Coimbatore -> Chennai", "Coimbatore", "Chennai", 10.93707, 76.95636, 13.08369, 80.27018),
    ("4. Chennai -> London", "Chennai", "London", 13.0827, 80.2707, 51.5074, -0.1278),
    ("5. New York -> London", "New York", "London", 40.7128, -74.0060, 51.5074, -0.1278),
    ("6. Seoul -> Tokyo", "Seoul", "Tokyo", 37.5665, 126.9780, 35.6762, 139.6503),
    ("7. Tokyo -> London", "Tokyo", "London", 35.6762, 139.6503, 51.5074, -0.1278),
    ("8. Delhi -> Paris", "New Delhi", "Paris", 28.6139, 77.2090, 48.8566, 2.3522),
    ("9. Chennai Central -> Chennai Central Metro (Same Location)", "Chennai Central", "Chennai Central Metro", 13.0827, 80.2707, 13.0829, 80.2709),
]

print("\n3. MULTIMODAL ROUTER SCENARIOS:")
for title, orig, dest, o_lat, o_lon, d_lat, d_lon in scenarios:
    print(f"\n--------------------------------------------------")
    print(f"SCENARIO: {title}")
    print(f"--------------------------------------------------")
    res = TransitOrchestrator.get_transit_plan(
        origin=orig, destination=dest,
        origin_lat=o_lat, origin_lon=o_lon,
        dest_lat=d_lat, dest_lon=d_lon,
        request_id=f"req_v12_2_{title[0]}"
    )
    print(f"status:           {res.get('status')}")
    print(f"journey_scale:    {res.get('journey_scale')}")
    print(f"provider_trace:   {res.get('provider_trace') or res.get('provider_info')}")
    
    j = res.get("journey")
    if j:
        print(f"SELECTED PROVIDER:{j.get('provider')} (MODE: {j.get('actual_mode')})")
        print(f"departure:        {j.get('departure_time')}")
        print(f"arrival:          {j.get('arrival_time')}")
        print(f"total distance:   {j.get('distance_km')} km")
    elif res.get("road_alternative"):
        print(f"SELECTED PROVIDER:OSRM Road Alternative ({res.get('road_alternative', {}).get('distance_km')} km)")
    elif res.get("route_guidance"):
        rg = res.get("route_guidance")
        print(f"SELECTED PROVIDER:[AI] Route Guidance (verified: {rg.get('verified')}, steps: {len(rg.get('steps', []))})")
    elif res.get("same_location"):
        print(f"SELECTED PROVIDER:[SAME_LOCATION] {res.get('message')}")
