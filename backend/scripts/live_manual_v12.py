import os
import sys
import json

# Force UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.transit.transit_orchestrator import TransitOrchestrator

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

for title, orig, dest, o_lat, o_lon, d_lat, d_lon in scenarios:
    print(f"\n==================================================")
    print(f"LIVE TEST V12.1 SCENARIO: {title}")
    print(f"==================================================")
    res = TransitOrchestrator.get_transit_plan(
        origin=orig, destination=dest,
        origin_lat=o_lat, origin_lon=o_lon,
        dest_lat=d_lat, dest_lon=d_lon,
        request_id=f"req_v12_1_{title[0]}"
    )
    print(f"request_id:       {res.get('request_id')}")
    print(f"status:           {res.get('status')}")
    print(f"journey_scale:    {res.get('journey_scale')}")
    print(f"origin:           {res.get('origin')}")
    print(f"destination:      {res.get('destination')}")
    
    j = res.get("journey")
    if j:
        print(f"provider:         {j.get('provider')}")
        print(f"departure:        {j.get('departure_time')}")
        print(f"arrival:          {j.get('arrival_time')}")
        print(f"total distance:   {j.get('distance_km')} km")
        print(f"transfers:        {j.get('transfers')}")
    elif res.get("road_alternative"):
        print(f"road_alternative: {res.get('road_alternative', {}).get('provider')} ({res.get('road_alternative', {}).get('distance_km')} km)")
    elif res.get("route_guidance"):
        rg = res.get("route_guidance")
        print(f"route_guidance:   [AI] Route Guidance (verified: {rg.get('verified')}, steps: {len(rg.get('steps', []))})")
    elif res.get("same_location"):
        print(f"same_location:    [SAME_LOCATION] {res.get('message')}")
    else:
        print("road_alternative: None (Suppressed)")
