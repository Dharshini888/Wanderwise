import sys, os
sys.path.insert(0, os.path.abspath("backend"))

from app.services.ai_service import generate_structured_itinerary
from app.routes.trips import _populate_trip_itinerary_from_ai
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.database.connection import Base
from datetime import date

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

# Let's call generate_structured_itinerary
print("Calling generate_structured_itinerary...")
ai_data = generate_structured_itinerary(
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

print("ai_data days count:", len(ai_data.get("days", [])))
inserted = _populate_trip_itinerary_from_ai(db, trip, ai_data)
print("Total inserted activities:", inserted)

days_in_db = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip.id).all()
print("Days in DB:", len(days_in_db))
for d in days_in_db:
    acts = db.query(ItineraryActivity).filter(ItineraryActivity.day_id == d.id).all()
    print(f"Day {d.day_number}: {len(acts)} activities")

from app.services.trip_service import enrich_trip_response
enriched = enrich_trip_response(trip, db)
print("Enriched activities_total:", enriched.get("activities_total"))
print("Enriched quick_insights:", enriched.get("quick_insights"))
for d in enriched.get("itinerary_days", []):
    print(f"Enriched Day {d.get('day_number')}: {len(d.get('activities', []))} activities | route_dist={d.get('route_distance_km')} | route_dur={d.get('route_duration_mins')}")

