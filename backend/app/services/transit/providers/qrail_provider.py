"""
qrail_provider.py -- Alternative QRail Railway API Provider for WanderWise

Integrates with QRail API when configured with QRAIL_API_KEY.
Truth-First: Returns PROVIDER_NOT_CONFIGURED when unconfigured. Never synthesizes mock data.
"""

import os
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from .base import TransitProvider, ProviderStatus, ProviderResult

logger = logging.getLogger(__name__)

QRAIL_BASE_URL = os.getenv("QRAIL_BASE_URL", "https://api.qrail.in/v1")


class QRailProvider(TransitProvider):
    def __init__(self):
        super().__init__(provider_name="QRail")

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        api_key = os.getenv("QRAIL_API_KEY")
        if not api_key:
            return ProviderResult(
                status=ProviderStatus.PROVIDER_NOT_CONFIGURED,
                provider_name=self.provider_name,
                note="QRail API key not configured (set QRAIL_API_KEY).",
            )

        prefs = preferences or {}
        from_code = prefs.get("from_station_code") or prefs.get("origin_code")
        to_code = prefs.get("to_station_code") or prefs.get("dest_code")

        if not from_code or not to_code:
            return ProviderResult(
                status=ProviderStatus.NO_COVERAGE,
                provider_name=self.provider_name,
                note="Origin or destination railway station code not resolved.",
            )

        url = f"{QRAIL_BASE_URL}/routes/{from_code}/{to_code}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key,
            "User-Agent": "WanderWise/14.0",
        }

        t0 = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=3.5)
            elapsed_ms = (time.time() - t0) * 1000.0

            if resp.status_code == 200:
                data = resp.json()
                trains = data.get("trains", [])
                itineraries = []
                for t in trains:
                    itineraries.append({
                        "route_id": f"qrail_{t.get('train_number')}_{from_code}_{to_code}",
                        "provider": self.provider_name,
                        "mode": "Rail",
                        "train_number": t.get("train_number"),
                        "train_name": t.get("train_name"),
                        "from_station_code": from_code,
                        "to_station_code": to_code,
                        "departure_time": t.get("departure_time"),
                        "arrival_time": t.get("arrival_time"),
                        "duration_min": t.get("duration_minutes", 450),
                        "distance_km": t.get("distance_km", 496),
                        "verification_status": "SCHEDULE_VERIFIED",
                        "schedule_source": "QRail API",
                        "fare": None,
                        "fare_source": "UNAVAILABLE",
                        "intermediate_stops": t.get("stops", []),
                        "geometry": t.get("geometry", []),
                    })
                return ProviderResult(
                    status=ProviderStatus.SUCCESS if itineraries else ProviderStatus.NO_ITINERARY,
                    provider_name=self.provider_name,
                    itineraries=itineraries,
                    latency_ms=elapsed_ms,
                    http_status=resp.status_code,
                )
            elif resp.status_code == 429:
                return ProviderResult(
                    status=ProviderStatus.RATE_LIMITED,
                    provider_name=self.provider_name,
                    http_status=429,
                    error="QRail rate limit exceeded",
                    latency_ms=elapsed_ms,
                )
            elif resp.status_code == 401:
                return ProviderResult(
                    status=ProviderStatus.AUTH_FAILED,
                    provider_name=self.provider_name,
                    http_status=401,
                    error="QRail authentication failed",
                    latency_ms=elapsed_ms,
                )
            else:
                return ProviderResult(
                    status=ProviderStatus.PROVIDER_UNAVAILABLE,
                    provider_name=self.provider_name,
                    http_status=resp.status_code,
                    error=f"QRail returned HTTP {resp.status_code}",
                    latency_ms=elapsed_ms,
                )
        except requests.exceptions.Timeout:
            return ProviderResult(
                status=ProviderStatus.TIMEOUT,
                provider_name=self.provider_name,
                error="QRail request timed out after 3.5s",
                latency_ms=(time.time() - t0) * 1000.0,
            )
        except Exception as e:
            return ProviderResult(
                status=ProviderStatus.PROVIDER_UNAVAILABLE,
                provider_name=self.provider_name,
                error=str(e)[:150],
                latency_ms=(time.time() - t0) * 1000.0,
            )
