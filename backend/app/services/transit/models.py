from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Fare(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    source: Optional[str] = None
    status: str = "UNAVAILABLE"

class Location(BaseModel):
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None

class LegBase(BaseModel):
    type: str
    provenance: str = "CALCULATED"

class WalkLeg(LegBase):
    type: str = "walk"
    from_loc: Location
    to_loc: Location
    distance_m: Optional[int] = None
    duration_minutes: Optional[int] = None
    navigation_available: bool = False

class TransferLeg(LegBase):
    type: str = "transfer"
    from_loc: Location
    to_loc: Location
    distance_m: Optional[int] = None
    duration_minutes: Optional[int] = None

class TransitLeg(LegBase):
    type: str = "transit"
    mode: str
    route_name: Optional[str] = None
    route_number: Optional[str] = None
    vehicle_id: Optional[str] = None
    boarding_stop: Location
    alighting_stop: Location
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    time_status: str = "UNAVAILABLE"
    platform: Optional[str] = None
    platform_status: str = "UNAVAILABLE"
    stops_count: Optional[int] = None
    headsign: Optional[str] = None

class Journey(BaseModel):
    origin: Location
    destination: Location
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    fare: Fare
    legs: List[Dict[str, Any]]
