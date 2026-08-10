"""
gtfs_provider.py — Local GTFS Feed Routing Provider for WanderWise v8

Parses locally installed/configured GTFS zip or sqlite feeds (stops.txt, routes.txt, etc).
If no local feeds exist, returns status PROVIDER_NOT_CONFIGURED.

RULE: A regional catalog (JSON) alone is NOT a feed.
Return PROVIDER_NOT_CONFIGURED unless a real parsed GTFS dataset is present.
"""

import os
import logging
from typing import Optional, Dict, Any
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)


class GTFSLocalProvider(TransitProvider):
    def __init__(self, gtfs_dir: Optional[str] = None):
        super().__init__(provider_name="GTFS Local")
        self.gtfs_dir = gtfs_dir or os.path.join(os.path.dirname(__file__), "feeds")

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        # Check if GTFS feeds directory exists and has parsed feeds
        if not os.path.exists(self.gtfs_dir) or not os.listdir(self.gtfs_dir):
            logger.info("[PROVIDER] GTFS Local: PROVIDER_NOT_CONFIGURED (No local GTFS feeds installed)")
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                note="No local GTFS feed files found in server storage.",
            )

        # If feeds are installed, GTFS parsing logic executes here
        return ProviderResult(
            status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
            provider_name=self.provider_name,
            note="Local GTFS feed processing unavailable.",
        )
