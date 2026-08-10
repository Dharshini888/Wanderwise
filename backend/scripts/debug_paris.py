import os
import sys
import requests
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.maps.nominatim_service import geocode_place

headers = {'User-Agent': 'WanderWise/9.2 (contact@wanderwise.ai)'}

print("=== DEBUG 1: Explicit London -> Paris ===")
geo_lon = geocode_place("London")
geo_par = geocode_place("Paris")
print(f"London coords: {geo_lon['lat']}, {geo_lon['lon']}")
print(f"Paris coords: {geo_par['lat']}, {geo_par['lon']}")

params_b = {
    'fromPlace': f"{geo_lon['lat']},{geo_lon['lon']}",
    'toPlace': f"{geo_par['lat']},{geo_par['lon']}",
    'numItineraries': 3,
    'mode': 'TRANSIT,WALK'
}
print(f"Transitous URL B: {params_b}")
r_b = requests.get("https://api.transitous.org/api/v1/plan", params=params_b, headers=headers, timeout=10)
print(f"HTTP status: {r_b.status_code}")
d_b = r_b.json()
its_b = d_b.get("itineraries", [])
print(f"London -> Paris itineraries count: {len(its_b)}")

print("\n=== DEBUG 2: GPS (51.5309, -0.1233) -> Paris ===")
params_a = {
    'fromPlace': '51.5309,-0.1233',
    'toPlace': f"{geo_par['lat']},{geo_par['lon']}",
    'numItineraries': 3,
    'mode': 'TRANSIT,WALK'
}
print(f"Transitous URL A: {params_a}")
r_a = requests.get("https://api.transitous.org/api/v1/plan", params=params_a, headers=headers, timeout=10)
print(f"HTTP status: {r_a.status_code}")
d_a = r_a.json()
its_a = d_a.get("itineraries", [])
print(f"GPS -> Paris itineraries count: {len(its_a)}")

if its_b:
    print("\nSample Legs in London -> Paris itinerary:")
    for idx, l in enumerate(its_b[0].get("legs", [])):
        f_track = l.get("from", {}).get("scheduledTrack") or l.get("from", {}).get("track") or l.get("from", {}).get("platformCode")
        print(f"  Leg {idx}: Mode={l.get('mode')}, Route={l.get('routeShortName') or l.get('routeLongName')}, From={l.get('from', {}).get('name')}, To={l.get('to', {}).get('name')}, Track={f_track}")
