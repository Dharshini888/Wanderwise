import sys, os, json
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

# Let's inspect what happens during _populate_trip_itinerary_from_ai when ai_data is empty or generated
# Test case 1: ai_data = {"days": []}
print("--- Case 1: Empty ai_data ---")
try:
    c = _populate_trip_itinerary_from_ai(db, trip, {"days": []})
    print("Case 1 result:", c)
except Exception as e:
    print("Case 1 exception:", type(e), e)

days1 = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip.id).all()
print(f"Case 1 DB Days: {len(days1)}")
for d in days1:
    acts = db.query(ItineraryActivity).filter(ItineraryActivity.day_id == d.id).all()
    print(f"  Day {d.day_number}: {len(acts)} activities")

