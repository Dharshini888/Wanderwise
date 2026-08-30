import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.database.connection import Base
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.place import Place
from app.services.trip_service import enrich_trip_response, resolve_and_enrich_itinerary_routes

# Setup in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_trip_map_transit_enrichment(db_session):
    # 1. Create a planned trip to Meghalaya
    trip = Trip(
        user_id=1,
        title="Meghalaya Expedition",
        destination="Meghalaya",
        country="India",
        origin_city="Coimbatore",
        start_date=date(2026, 10, 31),
        end_date=date(2026, 11, 5),
        budget=50000.0,
        currency="INR",
        status="Upcoming"
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    day1 = ItineraryDay(
        trip_id=trip.id,
        day_number=1,
        date=trip.start_date,
        title="Day 1: Shillong Attractions"
    )
    db_session.add(day1)
    db_session.commit()

    # Add places with verified test coordinates
    p1 = Place(name="Elephant Falls", city="Meghalaya", country="India", category="sightseeing", latitude=25.5378, longitude=91.8220)
    p2 = Place(name="Police Bazar", city="Meghalaya", country="India", category="shopping", latitude=25.5767, longitude=91.8814)
    db_session.add_all([p1, p2])
    db_session.commit()

    a1 = ItineraryActivity(day_id=day1.id, place_id=p1.id, order_index=0, title="Elephant Falls", transport_mode="Not available")
    a2 = ItineraryActivity(day_id=day1.id, place_id=p2.id, order_index=1, title="Police Bazar", transport_mode="Not available")
    db_session.add_all([a1, a2])
    db_session.commit()

    # 2. Call enrich_trip_response with live network enabled for single trip test
    enriched = enrich_trip_response(trip, db_session, fetch_live_network=True)

    # 3. Assert trip structure and route enrichment
    assert enriched["id"] == trip.id
    assert enriched["destination"] == "Meghalaya"
    assert len(enriched["itinerary_days"]) == 1
    
    day_res = enriched["itinerary_days"][0]
    assert "route_summary" in day_res
    route_sum = day_res["route_summary"]
    
    # Truth-First verification
    assert route_sum["stops_count"] >= 1
    assert "verification_status" in route_sum
