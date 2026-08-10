"""
navitia_provider.py — Secondary Transit Provider for WanderWise v8

Connects to Navitia IO API if NAVITIA_API_KEY environment variable is configured.
If unconfigured, safely returns PROVIDER_NOT_CONFIGURED status without crashing.
"""

import os
import requests
import logging
from typing import Optional, Dict, Any
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)


class NavitiaProvider(TransitProvider):
    def __init__(self):
        super().__init__(provider_name="Navitia")

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        api_key = os.getenv("NAVITIA_API_KEY")
        if not api_key:
            logger.info("[PROVIDER] Navitia: PROVIDER_NOT_CONFIGURED (No NAVITIA_API_KEY)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                note="Navitia API key is not configured in environment variables.",
            )

        url = f"https://api.navitia.io/v1/coverage/default/journeys"
        params = {
            "from": f"{origin_lon};{origin_lat}",
            "to": f"{dest_lon};{dest_lat}",
        }

        try:
            resp = requests.get(url, params=params, auth=(api_key, ""), timeout=8)
            if resp.status_code != 200:
                return ProviderResult(
                    status=ProviderStatus.PROVIDER_UNAVAILABLE,
                    provider_name=self.provider_name,
                    error=f"Navitia HTTP {resp.status_code}",
                )
            # Future Navitia parsing logic if key is supplied
            return ProviderResult(
                status=ProviderStatus.NO_ITINERARY,
                provider_name=self.provider_name,
                itineraries=[],
            )
        except Exception as e:
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=str(e)[:150],
            )
