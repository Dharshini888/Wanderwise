"""
base.py — WanderWise Provider Abstraction Interface

Defines standard provider status codes, normalized result structures, and
the abstract base class for all transit routing providers.

RULE: No provider may return None. Always return a structured ProviderResult.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ProviderStatus(str, Enum):
    SUCCESS = "SUCCESS"
    NO_COVERAGE = "NO_COVERAGE"
    NO_ITINERARY = "NO_ITINERARY"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_CONTRACT_UNVERIFIED = "PROVIDER_CONTRACT_UNVERIFIED"
    INVALID_REQUEST = "INVALID_REQUEST"


class ProviderResult(BaseModel):
    status: ProviderStatus
    provider_name: str
    itineraries: List[Dict[str, Any]] = []
    error: Optional[str] = None
    note: Optional[str] = None


class TransitProvider:
    """Abstract base class for all transit routing providers."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def plan_journey(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        raise NotImplementedError("Subclasses must implement plan_journey()")
