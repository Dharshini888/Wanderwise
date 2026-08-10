import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.transit.transit_orchestrator import TransitOrchestrator

scenarios = [
    ("1. London -> Manchester", "London Euston", "Manchester Piccadilly", 51.5309, -0.1233, 53.4774, -2.2309),
    ("2. London -> Paris", "London Euston", "Paris Gare du Nord", 51.5309, -0.1233, 48.8809, 2.3553),
    ("3. Coimbatore -> Chennai", "Coimbatore", "Chennai", 10.93707, 76.95636, 13.08369, 80.27018),
    ("4. Seoul -> Tokyo", "Seoul", "Tokyo", 37.5665, 126.9780, 35.6762, 139.6503),
    ("5. Tokyo -> London", "Tokyo", "London", 35.6762, 139.6503, 51.5074, -0.1278),
    ("6. Delhi -> Paris", "New Delhi", "Paris", 28.6139, 77.2090, 48.8566, 2.3522),
]

for title, orig, dest, o_lat, o_lon, d_lat, d_lon in scenarios:
    print(f"\n==================================================")
    print(f"LIVE TEST V11.1 SCENARIO: {title}")
    print(f"==================================================")
    res = TransitOrchestrator.get_transit_plan(
        origin=orig, destination=dest,
        origin_lat=o_lat, origin_lon=o_lon,
        dest_lat=d_lat, dest_lon=d_lon,
        request_id=f"req_v11_1_{title[0]}"
    )
    print(f"request_id:       {res.get('request_id')}")
    print(f"status:           {res.get('status')}")
    print(f"scale:            {res.get('scale')}")
    print(f"origin:           {res.get('origin')}")
    print(f"destination:      {res.get('destination')}")
    
    j = res.get("journey")
    if j:
        print(f"provider:         {j.get('provider')}")
        print(f"departure:        {j.get('departure_time')}")
        print(f"arrival:          {j.get('arrival_time')}")
        print(f"total distance:   {j.get('distance_km')} km")
        print(f"transfers:        {j.get('transfers')}")
    else:
        print("journey:           None")
        if res.get('road_alternative'):
            print(f"road_alternative: OSRM Driving ({res.get('road_alternative', {}).get('distance_km')} km)")
        else:
            print("road_alternative: None (Suppressed for International/Intercontinental)")
