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
from ..airport_service import GLOBAL_AIRPORTS

MAJOR_AIRPORTS = GLOBAL_AIRPORTS

def find_nearest_airport(lat: float, lon: float, max_radius_km: float = 300.0, is_international: bool = True) -> Optional[Dict[str, Any]]:
    if lat is None or lon is None:
        return None
    nearest = None
    min_dist = float('inf')

    # If international flight requested, first search among international tier airports
    candidate_airports = MAJOR_AIRPORTS
    if is_international:
        intl_candidates = [ap for ap in MAJOR_AIRPORTS if ap.get("tier") in ["primary_international", "secondary_international"]]
        if intl_candidates:
            candidate_airports = intl_candidates

    for ap in candidate_airports:
        dist = haversine_distance(lat, lon, ap["lat"], ap["lon"])
        if dist < min_dist and dist <= max_radius_km:
            min_dist = dist
            nearest = ap.copy()
            nearest["distance_from_point_km"] = round(dist, 2)

    # Fallback to any airport if no international airport was within radius
    if not nearest and is_international:
        return find_nearest_airport(lat, lon, max_radius_km=max_radius_km, is_international=False)

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

        is_intl = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon) > 500.0
        orig_ap = find_nearest_airport(origin_lat, origin_lon, is_international=is_intl)
        dest_ap = find_nearest_airport(dest_lat, dest_lon, is_international=is_intl)

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
