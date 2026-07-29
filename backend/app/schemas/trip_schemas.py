from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from app.core.currencies import CurrencyInfo

class CostSchema(BaseModel):
    amount: float = 0.0
    currency: str = "USD"
    symbol: Optional[str] = "$"
    estimated: bool = True

class Travelers(BaseModel):
    travel_type: str = "solo"
    adults: int = 1
    children: int = 0
    seniors: int = 0
    pets: int = 0
    group_size: int = 1

class Preferences(BaseModel):
    interests: List[str] = Field(default_factory=list)
    food_preferences: List[str] = Field(default_factory=list)
    food_allergies: List[str] = Field(default_factory=list)
    accessibility: List[str] = Field(default_factory=list)
    activity_pace: str = "balanced"
    ai_preferences: List[str] = Field(default_factory=list)
    daily_routine: Dict[str, Any] = Field(default_factory=dict)
    visa_status: str = "no_visa"

class WeatherContext(BaseModel):
    season: str = "Summer"
    temperature_range: str = "20C - 30C"
    rain_probability: int = 10
    weather_preference: str = "mix"

class LocalContext(BaseModel):
    festivals: List[str] = Field(default_factory=list)
    holidays: List[str] = Field(default_factory=list)
    peak_season: bool = False

class BudgetBreakdown(BaseModel):
    accommodation: float = 40.0
    food: float = 20.0
    transport: float = 20.0
    activities: float = 15.0
    emergency: float = 5.0

class AITripContext(BaseModel):
    destination: str
    country: str
    start_date: date
    end_date: date
    currency: CurrencyInfo
    budget: float
    travel_style: str = "solo"
    travelers: Travelers = Field(default_factory=Travelers)
    preferences: Preferences = Field(default_factory=Preferences)
    weather_context: WeatherContext = Field(default_factory=WeatherContext)
    local_context: LocalContext = Field(default_factory=LocalContext)
    budget_breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown)

class PlaceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    name: str
    category: str = "sightseeing"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[float] = 4.5
    opening_hours: Optional[str] = None
    ticket_price: Optional[float] = 0.0
    google_maps_url: Optional[str] = None
    osm_id: Optional[str] = None
    google_place_id: Optional[str] = None
    timezone: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    categories: Optional[str] = None

class ActivityCreate(BaseModel):
    day_id: int
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    time_slot: str = "morning"
    start_time: Optional[str] = "09:00"
    end_time: Optional[str] = "10:30"
    duration_minutes: Optional[int] = 90
    ticket_price: Optional[float] = 0.0
    transport_mode: Optional[str] = "Walking"
    transport_duration: Optional[str] = "15 mins"
    weather_suitability: Optional[str] = "Indoor"
    crowd_level: Optional[str] = "Moderate"
    ai_reason: Optional[str] = None
    place_name: Optional[str] = None
    place_category: Optional[str] = "sightseeing"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    activity_metadata: Optional[Dict[str, Any]] = None

class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_slot: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    ticket_price: Optional[float] = None
    transport_mode: Optional[str] = None
    weather_suitability: Optional[str] = None
    crowd_level: Optional[str] = None
    is_locked: Optional[bool] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    day_id: int
    place_id: Optional[int] = None
    time_slot: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = 90
    order_index: int
    title: str
    description: Optional[str] = None
    estimated_duration: Optional[str] = None
    ticket_price: float = 0.0
    cost: Optional[CostSchema] = None
    formatted_cost: Optional[str] = "$0"
    transport_mode: Optional[str] = "Walking"
    transport_duration: Optional[str] = None
    weather_suitability: Optional[str] = "Indoor"
    crowd_level: Optional[str] = "Moderate"
    ai_reason: Optional[str] = None
    confidence_score: Optional[float] = 0.95
    is_locked: bool = False
    place: Optional[PlaceSchema] = None
    metadata: Optional[Dict[str, Any]] = None

class ItineraryDayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_id: int
    day_number: int
    date: date
    title: Optional[str] = None
    theme_note: Optional[str] = None
    activities: List[ActivityResponse] = []

class ActivityReorder(BaseModel):
    activity_id: int
    target_day_id: int
    target_time_slot: str
    new_order_index: int

class TripCreate(BaseModel):
    user_id: int
    title: Optional[str] = None
    destination: str = Field(..., min_length=2)
    country: Optional[str] = None
    origin_city: Optional[str] = "Coimbatore"
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    start_date: date
    end_date: date
    budget: float = Field(..., gt=0)
    currency: str = "USD"
    travel_type: Optional[str] = "leisure"
    travel_style: Optional[str] = "solo"
    transportation: Optional[str] = "flight"
    accommodation_preference: Optional[str] = "hotel"
    interests: Optional[str] = "sightseeing, food"
    travel_companion: Optional[str] = "solo"
    group_size: int = Field(1, ge=1)
    visibility: Optional[str] = "private"
    notes: Optional[str] = None
    color_theme: Optional[str] = "blue"
    image_url: Optional[str] = None
    force_create: bool = False
    is_budget_friendly: bool = False
    trip_preferences: Optional[Dict[str, Any]] = None

class TripUpdate(BaseModel):
    title: Optional[str] = None
    destination: Optional[str] = None
    country: Optional[str] = None
    origin_city: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    travel_type: Optional[str] = None
    travel_style: Optional[str] = None
    transportation: Optional[str] = None
    accommodation_preference: Optional[str] = None
    interests: Optional[str] = None
    travel_companion: Optional[str] = None
    group_size: Optional[int] = None
    visibility: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    color_theme: Optional[str] = None
    image_url: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    trip_preferences: Optional[Dict[str, Any]] = None

class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: Optional[str] = None
    destination: str
    country: Optional[str] = None
    origin_city: Optional[str] = "Coimbatore"
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    start_date: date
    end_date: date
    budget: float
    currency: str = "USD"
    currency_symbol: str = "$"
    travel_type: Optional[str] = "leisure"
    travel_style: Optional[str] = "solo"
    transportation: Optional[str] = "flight"
    accommodation_preference: Optional[str] = "hotel"
    interests: Optional[str] = None
    travel_companion: Optional[str] = None
    group_size: int = 1
    visibility: str = "private"
    notes: Optional[str] = None
    status: str = "Upcoming"
    is_favorite: bool = False
    is_archived: bool = False
    color_theme: Optional[str] = "blue"
    image_url: Optional[str] = None
    share_token: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    trip_preferences: Optional[Dict[str, Any]] = None
    
    # Calculated properties
    number_of_days: int = 1
    days_left: int = 0
    trip_progress: float = 0.0
    countdown: str = ""
    estimated_daily_budget: float = 0.0
    budget_per_person: float = 0.0
    total_budget_remaining: float = 0.0
    itinerary_days: List[ItineraryDayResponse] = []

class DashboardWidgetResponse(BaseModel):
    version: str = "1.0"
    active_trip: Optional[TripResponse] = None
    upcoming_trips_count: int = 0
    days_to_next_flight: Optional[int] = None
    budget_remaining: float = 0.0
    total_budget: float = 0.0
    currency: str = "USD"
    trip_progress: float = 0.0
    today_plan: List[ActivityResponse] = []
    quick_actions: List[str] = [
        "Create Trip", "Add Expense", "Check Packing", "View Safety Alerts", "Convert Currency"
    ]

class GenerateItineraryRequest(BaseModel):
    force: bool = True


class RegenerateDayRequest(BaseModel):
    day_number: int
    notes: Optional[str] = None

class SearchTripsRequest(BaseModel):
    query: str
    user_id: int

class FilterTripsRequest(BaseModel):
    user_id: int
    status: Optional[str] = None
    travel_style: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
