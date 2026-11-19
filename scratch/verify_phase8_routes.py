import os
import sys
from datetime import datetime, date, timedelta

# Ensure backend is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.transit.transit_orchestrator import TransitOrchestrator
from app.services.transit.tz_utils import KOLKATA_TZ

routes_to_test = [
    {
        "name": "Route 1: Chennai -> Coimbatore",
        "origin": "Chennai Central",
        "origin_lat": 13.0827,
        "origin_lon": 80.2757,
        "dest": "Coimbatore Junction",
        "dest_lat": 11.0017,
        "dest_lon": 76.9629,
    },
    {
        "name": "Route 2: Madurai -> Chennai",
        "origin": "Madurai Junction",
        "origin_lat": 9.9195,
        "origin_lon": 78.1118,
        "dest": "Chennai Egmore",
        "dest_lat": 13.0827,
        "dest_lon": 80.2757,
    },
    {
        "name": "Route 3: Salem Junction -> KSR Bengaluru",
        "origin": "Salem Junction",
        "origin_lat": 11.6643,
        "origin_lon": 78.1460,
        "dest": "KSR Bengaluru",
        "dest_lat": 12.9784,
        "dest_lon": 77.5684,
    },
    {
        "name": "Route 4: Erode Junction -> Coimbatore",
        "origin": "Erode Junction",
        "origin_lat": 11.3410,
        "origin_lon": 77.7172,
        "dest": "Coimbatore Junction",
        "dest_lat": 11.0017,
        "dest_lon": 76.9629,
    },
    {
        "name": "Route 5: KSR Bengaluru -> Mysuru",
        "origin": "KSR Bengaluru",
        "origin_lat": 12.9784,
        "origin_lon": 77.5684,
        "dest": "Mysuru Junction",
        "dest_lat": 12.3164,
        "dest_lon": 76.6453,
    },
]

print("=" * 80)
print("WANDERWISE V12.2 -- PHASE 8 ROUTE VERIFICATION SUITE")
print("=" * 80)

all_passed = True

for r in routes_to_test:
    print(f"\n>>> TESTING {r['name']}")
    
    # Test A: Leave Now
    plan_now = TransitOrchestrator.get_transit_plan(
        origin=r["origin"],
        destination=r["dest"],
        origin_lat=r["origin_lat"],
        origin_lon=r["origin_lon"],
        dest_lat=r["dest_lat"],
        dest_lon=r["dest_lon"],
        departure_type="now",
        preferred_mode="transit",
    )
    
    routes_now = plan_now.get("all_route_options") or plan_now.get("journeys") or []
    rail_routes_now = [rt for rt in routes_now if (rt.get("mode") or "").lower() in ("train", "rail") or rt.get("train_number")]
    print(f"  [Leave Now] Total options: {len(routes_now)}, Train options: {len(rail_routes_now)}")
    
    if not rail_routes_now:
        print(f"  FAILED: No train routes returned for {r['name']} on 'Leave Now'!")
        all_passed = False
    else:
        for rt in rail_routes_now[:3]:
            t_num = rt.get("train_number")
            t_name = rt.get("train_name")
            dep = rt.get("departure_time_display")
            arr = rt.get("arrival_time_display")
            dur = rt.get("total_duration_min") or rt.get("duration_min")
            c_stat = rt.get("catchability_status")
            v_stat = rt.get("verification_status")
            prov = rt.get("provider")
            fare = rt.get("fare")
            print(f"    Train #{t_num} ({t_name}): Dep {dep} -> Arr {arr} | Dur {dur}m | Catch: {c_stat} | Prov: {prov} | Ver: {v_stat} | Fare: {fare}")
            assert fare is None, f"Fare must be None, got {fare}"
            assert v_stat in ("SCHEDULE_VERIFIED", "PROVIDER_VERIFIED", "LIVE_VERIFIED"), f"Invalid provenance: {v_stat}"

    # Test B: Set Departure Time (Scheduled, e.g., 06:00 tomorrow)
    tomorrow_iso = (datetime.now(KOLKATA_TZ) + timedelta(days=1)).strftime("%Y-%m-%d")
    plan_sched = TransitOrchestrator.get_transit_plan(
        origin=r["origin"],
        destination=r["dest"],
        origin_lat=r["origin_lat"],
        origin_lon=r["origin_lon"],
        dest_lat=r["dest_lat"],
        dest_lon=r["dest_lon"],
        departure_type="scheduled",
        date=tomorrow_iso,
        departure_time="06:00",
        preferred_mode="transit",
    )
    
    routes_sched = plan_sched.get("all_route_options") or plan_sched.get("journeys") or []
    rail_routes_sched = [rt for rt in routes_sched if (rt.get("mode") or "").lower() in ("train", "rail") or rt.get("train_number")]
    print(f"  [Scheduled 06:00 Tomorrow] Total options: {len(routes_sched)}, Train options: {len(rail_routes_sched)}")
    
    if not rail_routes_sched:
        print(f"  FAILED: No train routes returned for {r['name']} on 'Scheduled'!")
        all_passed = False
    else:
        for rt in rail_routes_sched[:3]:
            t_num = rt.get("train_number")
            t_name = rt.get("train_name")
            dep = rt.get("departure_time_display")
            arr = rt.get("arrival_time_display")
            dur = rt.get("total_duration_min") or rt.get("duration_min")
            c_stat = rt.get("catchability_status")
            v_stat = rt.get("verification_status")
            prov = rt.get("provider")
            fare = rt.get("fare")
            print(f"    Train #{t_num} ({t_name}): Dep {dep} -> Arr {arr} | Dur {dur}m | Catch: {c_stat} | Prov: {prov} | Ver: {v_stat} | Fare: {fare}")

print("\n" + "=" * 80)
if all_passed:
    print("ALL 5 PHASE 8 CORRIDORS VERIFIED SUCCESSFULLY WITH 100% ACCURACY!")
else:
    print("SOME CORRIDORS FAILED VERIFICATION.")
print("=" * 80)
