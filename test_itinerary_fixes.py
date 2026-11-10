import os
import sys
from datetime import date, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database.connection import SessionLocal, Base, engine
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.schemas.trip_schemas import TripCreate
from app.services.trip_service import create_trip
from app.routes.trips import _populate_trip_itinerary_from_ai
from app.services.ai_service import generate_structured_itinerary


def test_itinerary_generation():
    db = SessionLocal()
    try:
        print("\n=======================================================")
        print("TEST CASE 1: Trip Destination = Hawaii, Start Date = 2026-10-01")
        print("=======================================================")

        # Create Hawaii Trip
        trip_hawaii_data = TripCreate(
            user_id=1,
            destination="Hawaii",
            country="United States",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 3),
            budget=3000.0,
            currency="USD",
            interests="Beaches, Sightseeing, Local Dining"
        )

        trip_h = create_trip(db, trip_hawaii_data)

        # Generate structured itinerary
        ai_data_h = generate_structured_itinerary(
            destination="Hawaii",
            days=3,
            budget=3000.0,
            interests="Beaches, Sightseeing, Local Dining",
            travel_style="solo",
            currency="USD",
            start_date="2026-10-01",
            end_date="2026-10-03"
        )

        _populate_trip_itinerary_from_ai(db, trip_h, ai_data_h)
        db.refresh(trip_h)

        print(f"\nTrip ID: {trip_h.id} | Destination: {trip_h.destination}")
        for day in trip_h.itinerary_days:
            clean_day_title = day.title.encode('ascii', 'ignore').decode('ascii')
            print(f"\n--- Day {day.day_number} ({day.date}) Title: {clean_day_title} ---")
            assert str(day.date) == str(date(2026, 10, 1) + timedelta(days=day.day_number - 1)), f"Date mismatch for Day {day.day_number}!"

            for act in day.activities:
                p_name = act.place.name if act.place else act.title
                p_city = act.place.city if act.place else ""
                maps_url = act.place.google_maps_url if act.place else ""

                clean_title = act.title.encode('ascii', 'ignore').decode('ascii')
                clean_pname = p_name.encode('ascii', 'ignore').decode('ascii')
                clean_pcity = p_city.encode('ascii', 'ignore').decode('ascii')
                print(f"  [{act.start_time} - {act.end_time}] ({act.duration_minutes}m) {clean_title} @ {clean_pname} ({clean_pcity})")
                print(f"    Maps URL: {maps_url}")
                if act.transport_mode:
                    print(f"    Travel transition: {act.transport_mode} ({act.transport_duration}) -> {act.activity_metadata.get('next_place_name') or 'Next'}")
                else:
                    print(f"    Final Activity of the Day (No travel transition)")

                # Verify Hawaii activity DOES NOT contain Tokyo or Skytree or Senso-ji
                assert "tokyo" not in p_name.lower(), f"CROSS-CITY LEAKAGE: Tokyo place '{p_name}' found in Hawaii trip!"
                assert "tokyo" not in maps_url.lower(), f"CONTRADICTORY MAPS URL: '{maps_url}' found in Hawaii trip!"
                assert "tokyo hawaii" not in maps_url.lower(), f"CONTRADICTORY MAPS URL: '{maps_url}'"

                # Verify start/end time math
                st_parts = act.start_time.split(":")
                et_parts = act.end_time.split(":")
                st_mins = int(st_parts[0]) * 60 + int(st_parts[1])
                et_mins = int(et_parts[0]) * 60 + int(et_parts[1])
                assert et_mins == st_mins + act.duration_minutes, f"TIME MATH CONTRADICTION: {act.start_time} + {act.duration_minutes}m != {act.end_time}"

                # Verify semantic titles
                if "sunset" in act.title.lower():
                    assert 16 * 60 <= st_mins <= 20 * 60, f"SEMANTIC MISMATCH: Sunset activity scheduled at {act.start_time}!"
                if "breakfast" in act.title.lower():
                    assert 6 * 60 <= st_mins <= 10 * 60, f"SEMANTIC MISMATCH: Breakfast activity scheduled at {act.start_time}!"
                if "lunch" in act.title.lower():
                    assert 11 * 60 <= st_mins <= 14 * 60 + 30, f"SEMANTIC MISMATCH: Lunch activity scheduled at {act.start_time}!"

        print("\n[SUCCESS] HAWAII TRIP ITINERARY TEST PASSED 100%!")

        print("\n=======================================================")
        print("TEST CASE 2: Trip Destination = Tokyo, Start Date = 2026-10-01")
        print("=======================================================")

        # Create Tokyo Trip
        trip_tokyo_data = TripCreate(
            user_id=1,
            destination="Tokyo",
            country="Japan",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
            budget=2000.0,
            currency="USD",
            interests="Culture, Food, Observation Decks"
        )

        trip_t = create_trip(db, trip_tokyo_data)

        # Generate structured itinerary
        ai_data_t = generate_structured_itinerary(
            destination="Tokyo",
            days=2,
            budget=2000.0,
            interests="Culture, Food, Observation Decks",
            travel_style="solo",
            currency="USD",
            start_date="2026-10-01",
            end_date="2026-10-02"
        )

        _populate_trip_itinerary_from_ai(db, trip_t, ai_data_t)
        db.refresh(trip_t)

        print(f"\nTrip ID: {trip_t.id} | Destination: {trip_t.destination}")
        for day in trip_t.itinerary_days:
            clean_day_title = day.title.encode('ascii', 'ignore').decode('ascii')
            print(f"\n--- Day {day.day_number} ({day.date}) Title: {clean_day_title} ---")
            assert str(day.date) == str(date(2026, 10, 1) + timedelta(days=day.day_number - 1)), f"Date mismatch for Day {day.day_number}!"

            for act in day.activities:
                p_name = act.place.name if act.place else act.title
                p_city = act.place.city if act.place else ""
                maps_url = act.place.google_maps_url if act.place else ""

                clean_title = act.title.encode('ascii', 'ignore').decode('ascii')
                clean_pname = p_name.encode('ascii', 'ignore').decode('ascii')
                clean_pcity = p_city.encode('ascii', 'ignore').decode('ascii')
                print(f"  [{act.start_time} - {act.end_time}] ({act.duration_minutes}m) {clean_title} @ {clean_pname} ({clean_pcity})")
                print(f"    Maps URL: {maps_url}")

                assert "hawaii" not in p_name.lower(), f"CROSS-CITY LEAKAGE: Hawaii place '{p_name}' found in Tokyo trip!"
                assert "hawaii" not in maps_url.lower(), f"CONTRADICTORY MAPS URL: '{maps_url}'"

        print("\n[SUCCESS] TOKYO TRIP ITINERARY TEST PASSED 100%!")

    finally:
        db.close()


if __name__ == "__main__":
    test_itinerary_generation()
