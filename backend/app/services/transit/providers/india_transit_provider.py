"""
india_transit_provider.py — Indian Transit Provider for WanderWise v9

Checks for Indian transit / RailRadar API configurations in environment variables.
If unconfigured or unreachable, safely returns PROVIDER_NOT_CONFIGURED status.
Never fabricates fake Indian train schedules.
"""

import os
import requests
import logging
from typing import Optional, Dict, Any
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)


class IndiaTransitProvider(TransitProvider):
    def __init__(self):
        super().__init__(provider_name="India Transit")

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        api_key = os.getenv("RAILRADAR_API_KEY") or os.getenv("INDIAN_RAILWAYS_API_KEY")
        if not api_key:
            logger.info("[PROVIDER] India Transit: PROVIDER_NOT_CONFIGURED (No active Indian transit API key)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                note="Indian transit provider API key is unconfigured in server environment.",
            )

        # Provider endpoint verification if key exists
        try:
            # RailRadar / Indian transit schedule lookup attempt
            headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "WanderWise/9.0"}
            # Example API call placeholder for configured RailRadar credentials
            url = f"https://api.railradar.in/v1/search?from={origin_lat},{origin_lon}&to={dest_lat},{dest_lon}"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("journeys"):
                    return ProviderResult(
                        status=ProviderStatus.SUCCESS,
                        provider_name=self.provider_name,
                        itineraries=data.get("journeys", []),
                    )
            
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
                note="No Indian transit itineraries returned for this route.",
            )
        except Exception as e:
            logger.warning(f"[PROVIDER] India Transit: PROVIDER_UNAVAILABLE ({e})")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=str(e)[:150],
                note="Indian transit provider endpoint unreachable.",
            )
