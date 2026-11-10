import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from app.services.ai_service import generate_structured_itinerary
from app.database.connection import SessionLocal
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.routes.trips import _populate_trip_itinerary_from_ai, create_new_trip, resolve_trip_preferences
from app.schemas.trip_schemas import TripCreate
from datetime import date

print("=== 1. Testing generate_structured_itinerary for Singapore ===")
res = generate_structured_itinerary(
    destination="Singapore",
    days=6,
    budget=200000.0,
    currency="INR",
    group_size=3,
    interests="Nature, Photography, Adventure, Shopping",
    travel_style="family",
    origin_city="Coimbatore",
    start_date="2026-12-10",
    end_date="2026-12-15",
    trip_preferences={"travelers": {"adults": 2, "children": 1, "child_ages": [10]}}
)
days = res.get("days", [])
print(f"Total days returned: {len(days)}")
for d in days:
    acts = d.get("activities", [])
    print(f"Day {d.get('day_number')}: {len(acts)} activities")
    for a in acts[:2]:
        print(f"   - {a.get('title')} ({a.get('start_time')})")

print("\n=== 2. Testing _populate_trip_itinerary_from_ai ===")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.database.connection import Base
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)
db = TestingSessionLocal()

trip = Trip(
    user_id=1,
    destination="Singapore",
    country="Singapore",
    start_date=date(2026, 12, 10),
    end_date=date(2026, 12, 15),
    budget=200000.0,
    currency="INR",
    group_size=3,
    trip_preferences={"travelers": {"adults": 2, "children": 1, "child_ages": [10]}}
)
db.add(trip)
db.commit()
db.refresh(trip)

inserted = _populate_trip_itinerary_from_ai(db, trip, res)
print(f"Total inserted activities: {inserted}")
db_days = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip.id).all()
print(f"Total DB days: {len(db_days)}")
for dd in db_days:
    db_acts = db.query(ItineraryActivity).filter(ItineraryActivity.day_id == dd.id).all()
    print(f"DB Day {dd.day_number}: {len(db_acts)} activities")

from app.services.trip_service import enrich_trip_response
enriched = enrich_trip_response(trip, db)
print(f"Enriched activities_total: {enriched.get('activities_total')}")
print(f"Enriched quick_insights: {enriched.get('quick_insights')}")
for ed in enriched.get("itinerary_days", []):
    print(f"Enriched Day {ed.get('day_number')}: {len(ed.get('activities', []))} activities | Route Distance: {ed.get('route_distance_km')} km | Dur: {ed.get('route_duration_mins')} mins")
