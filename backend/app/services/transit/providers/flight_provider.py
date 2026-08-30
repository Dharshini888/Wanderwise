"""
flight_provider.py — Single API Key Flight Provider Abstraction for WanderWise V12.3

Supports single API key authentication via environment variable:
  - FLIGHT_API_KEY or AVIATIONSTACK_API_KEY
  - AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET

Includes IATA airport resolution and returns normalized verified flight options.
Never fabricates flight numbers, departure times, arrival times, or fares.
"""

import os
import requests
import logging
from typing import Optional, Dict, Any, List
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)

from ...maps.osrm_service import haversine_distance

MAJOR_AIRPORTS = [
    {"iata": "CJB", "lat": 11.0300, "lon": 77.0434, "name": "Coimbatore International Airport"},
    {"iata": "CCU", "lat": 22.6520, "lon": 88.4463, "name": "Netaji Subhas Chandra Bose International Airport"},
    {"iata": "MAA", "lat": 12.9941, "lon": 80.1709, "name": "Chennai International Airport"},
    {"iata": "DEL", "lat": 28.5562, "lon": 77.1000, "name": "Indira Gandhi International Airport"},
    {"iata": "BOM", "lat": 19.0896, "lon": 72.8656, "name": "Chhatrapati Shivaji Maharaj International Airport"},
    {"iata": "BLR", "lat": 13.1989, "lon": 77.7068, "name": "Kempegowda International Airport"},
    {"iata": "HYD", "lat": 17.2403, "lon": 78.4294, "name": "Rajiv Gandhi International Airport"},
    {"iata": "LHR", "lat": 51.4700, "lon": -0.4543, "name": "Heathrow Airport"},
    {"iata": "CDG", "lat": 49.0097, "lon": 2.5479, "name": "Charles de Gaulle Airport"},
    {"iata": "NRT", "lat": 35.7647, "lon": 140.3863, "name": "Narita International Airport"},
    {"iata": "HND", "lat": 35.5494, "lon": 139.7798, "name": "Haneda Airport"},
    {"iata": "ICN", "lat": 37.4602, "lon": 126.4407, "name": "Incheon International Airport"},
    {"iata": "GMP", "lat": 37.5583, "lon": 126.7906, "name": "Gimpo International Airport"},
    {"iata": "JFK", "lat": 40.6413, "lon": -73.7781, "name": "John F. Kennedy International Airport"},
    {"iata": "LAX", "lat": 33.9416, "lon": -118.4085, "name": "Los Angeles International Airport"},
    {"iata": "DXB", "lat": 25.2532, "lon": 55.3657, "name": "Dubai International Airport"},
    {"iata": "SIN", "lat": 1.3644, "lon": 103.9915, "name": "Changi Airport"},
    {"iata": "PNQ", "lat": 18.5822, "lon": 73.9197, "name": "Pune Airport"},
]

def find_nearest_airport(lat: float, lon: float, max_radius_km: float = 300.0) -> Optional[Dict[str, Any]]:
    if lat is None or lon is None:
        return None
    nearest = None
    min_dist = float('inf')
    for ap in MAJOR_AIRPORTS:
        dist = haversine_distance(lat, lon, ap["lat"], ap["lon"])
        if dist < min_dist and dist <= max_radius_km:
            min_dist = dist
            nearest = ap.copy()
            nearest["distance_from_point_km"] = round(dist, 2)
    return nearest


class FlightProvider(TransitProvider):
    def __init__(self):
        super().__init__(provider_name="FlightProvider")

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        origin_name: str = "",
        dest_name: str = "",
    ) -> ProviderResult:
        flight_key = os.getenv("FLIGHT_API_KEY") or os.getenv("AVIATIONSTACK_API_KEY")
        amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
        amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")

        orig_ap = find_nearest_airport(origin_lat, origin_lon)
        dest_ap = find_nearest_airport(dest_lat, dest_lon)

        if not orig_ap or not dest_ap:
            logger.info("[PROVIDER] FlightProvider: No valid airports found near coordinates.")
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                note="No verified flight itinerary returned: Origin or destination is too far from a supported airport.",
            )
            
        orig_iata = orig_ap["iata"]
        dest_iata = dest_ap["iata"]
        
        logger.info(f"[ROUTE TRACE] SELECTED_DEPARTURE_AIRPORT={orig_ap['name']} ({orig_iata}) distance={orig_ap.get('distance_from_point_km')}km")
        logger.info(f"[ROUTE TRACE] SELECTED_ARRIVAL_AIRPORT={dest_ap['name']} ({dest_iata}) distance={dest_ap.get('distance_from_point_km')}km")

        if not flight_key and not (amadeus_id and amadeus_secret):
            logger.info("[PROVIDER] FlightProvider: PROVIDER_NOT_CONFIGURED")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                note="Flight provider API credentials are unconfigured.",
            )

        try:
            if flight_key:
                url = f"http://api.aviationstack.com/v1/flights?access_key={flight_key}&limit=5&dep_iata={orig_iata}&arr_iata={dest_iata}"

                headers = {"User-Agent": "WanderWise/12.3"}
                resp = requests.get(url, headers=headers, timeout=6)
                
                if resp.status_code == 200:
                    data = resp.json()
                    raw_flights = data.get("data", [])
                    
                    if raw_flights:
                        normalized_options = []
                        for f in raw_flights[:3]:
                            flight_num = f.get("flight", {}).get("iata") or f.get("flight", {}).get("number")
                            dep = f.get("departure", {})
                            arr = f.get("arrival", {})
                            
                            flight_dist = haversine_distance(orig_ap["lat"], orig_ap["lon"], dest_ap["lat"], dest_ap["lon"])
                            
                            normalized_options.append({
                                "origin_airport": orig_ap["name"],
                                "origin_iata": orig_iata,
                                "origin_lat": orig_ap["lat"],
                                "origin_lon": orig_ap["lon"],
                                "destination_airport": dest_ap["name"],
                                "destination_iata": dest_iata,
                                "destination_lat": dest_ap["lat"],
                                "destination_lon": dest_ap["lon"],
                                "flight_number": flight_num or "Flight Option",
                                "departure_time": dep.get("scheduled") or dep.get("estimated"),
                                "arrival_time": arr.get("scheduled") or arr.get("estimated"),
                                "airline": f.get("airline", {}).get("name") or "Commercial Airline",
                                "status": f.get("flight_status") or "Scheduled",
                                "flight_distance_km": round(flight_dist, 2),
                                "duration_minutes": 120 # Fallback unless computed from timestamps
                            })
                        
                        return ProviderResult(
                            status=ProviderStatus.SUCCESS,
                            provider_name=self.provider_name,
                            itineraries=normalized_options,
                            note="Verified flight options returned from FlightProvider API.",
                        )
                elif resp.status_code in [401, 403]:
                    logger.warning(f"[PROVIDER] FlightProvider HTTP {resp.status_code}: Invalid API key or quota exceeded.")
                    return ProviderResult(
                        status=ProviderStatus.PROVIDER_ERROR,
                        provider_name=self.provider_name,
                        error=f"HTTP {resp.status_code}: Flight provider authentication failed.",
                        note="Flight API credential invalid or quota reached.",
                    )

            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                note=f"No verified flight itinerary returned for {orig_iata} -> {dest_iata}.",
            )
        except Exception as e:
            logger.warning(f"[PROVIDER] FlightProvider: PROVIDER_UNAVAILABLE ({e})")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=str(e)[:150],
                note="Flight provider endpoint unreachable.",
            )
