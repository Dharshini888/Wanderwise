import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.transit.transit_orchestrator import TransitOrchestrator

scenarios = [
    ("A. London -> Manchester", "London Euston", "Manchester Piccadilly", 51.5309, -0.1233, 53.4774, -2.2309),
    ("B. London -> Paris", "London Euston", "Paris Gare du Nord", 51.5309, -0.1233, 48.8809, 2.3553),
    ("C. Coimbatore -> Chennai", "Coimbatore", "Chennai", 10.93707, 76.95636, 13.08369, 80.27018),
    ("D. Current GPS -> Paris", "Current Location", "Paris", 11.0, 77.0, 48.8588, 2.3200),
]

for title, orig, dest, o_lat, o_lon, d_lat, d_lon in scenarios:
    print(f"\n==================================================")
    print(f"LIVE TEST SCENARIO: {title}")
    print(f"==================================================")
    res = TransitOrchestrator.get_transit_plan(
        origin=orig, destination=dest,
        origin_lat=o_lat, origin_lon=o_lon,
        dest_lat=d_lat, dest_lon=d_lon,
        request_id=f"req_live_{title[0].lower()}"
    )
    print(f"request_id:       {res.get('request_id')}")
    print(f"status:           {res.get('status')}")
    print(f"origin:           {res.get('origin')}")
    print(f"destination:      {res.get('destination')}")
    
    j = res.get("journey")
    if j:
        print(f"provider:         {j.get('provider')}")
        print(f"departure:        {j.get('departure_time')}")
        print(f"arrival:          {j.get('arrival_time')}")
        print(f"total distance:   {j.get('distance_km')} km")
        print(f"walking distance: {j.get('walking_distance_km')} km")
        print(f"transit distance: {j.get('transit_distance_km')} km")
        print(f"movement duration:{j.get('movement_duration_minutes')} min")
        print(f"waiting duration: {j.get('waiting_duration_minutes')} min")
        print(f"transfers:        {j.get('transfers')}")
        
        legs = j.get("legs", [])
        transit_legs = [l for l in legs if l.get("type") == "TRANSIT"]
        if transit_legs:
            l0 = transit_legs[0]
            print(f"platform (sample):{l0.get('platform')}")
            print(f"platform_source:  {l0.get('platform_source')}")
            print(f"distance_source:  {l0.get('distance_source')}")
            print(f"distance_type:    {l0.get('distance_type')}")
    else:
        print("journey:           None")
        print(f"road_alternative: {res.get('road_alternative', {}).get('provider')} ({res.get('road_alternative', {}).get('distance_km')} km)")
        print(f"fallback status:  {res.get('status')}")
    
    print(f"data_quality:     {json.dumps(res.get('data_quality', {}), indent=2)}")
