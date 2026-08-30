import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from app.services.maps.osrm_service import haversine_distance

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

cities = {
    "Coimbatore": (11.0168, 76.9558),
    "Pune": (18.5204, 73.8567),
    "Mumbai": (19.0760, 72.8777),
    "Kolkata": (22.5726, 88.3639),
}

query_template = """
[out:json][timeout:6];
(
  node(around:5000,{lat},{lon})["highway"~"bus_stop|bus_station"];
  way(around:5000,{lat},{lon})["highway"~"bus_stop|bus_station"];
  node(around:5000,{lat},{lon})["railway"~"station|halt"];
  way(around:5000,{lat},{lon})["railway"~"station|halt"];
  node(around:5000,{lat},{lon})["amenity"~"taxi|parking|ev_charging"];
);
out center 10;
"""

for city_name, (lat, lon) in cities.items():
    print(f"\n--- {city_name} ({lat}, {lon}) ---")
    query = query_template.format(lat=lat, lon=lon)
    success = False
    for server in OVERPASS_SERVERS:
        try:
            resp = requests.post(server, data={"data": query}, timeout=6.0)
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                print(f"Success from {server}: {len(elements)} elements found.")
                for el in elements[:4]:
                    tags = el.get("tags", {})
                    name = tags.get("name") or "Local Transit Spot"
                    t = tags.get("highway") or tags.get("railway") or tags.get("amenity")
                    p_lat = el.get("lat") or el.get("center", {}).get("lat")
                    p_lon = el.get("lon") or el.get("center", {}).get("lon")
                    dist = haversine_distance(lat, lon, p_lat, p_lon) if p_lat and p_lon else 0.0
                    print(f"  • {name} [{t}] - {dist:.2f} km @ ({p_lat}, {p_lon})")
                success = True
                break
        except Exception as e:
            print(f"Server {server} failed: {e}")
    if not success:
        print("All servers failed or timed out.")
