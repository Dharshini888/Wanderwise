import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.trip import Trip
from app.services.trip_service import enrich_trip_response

def verify_api_trips_payload():
    print("=== INSPECTING GET /api/trips BACKEND API PAYLOAD ===")
    db = SessionLocal()
    try:
        trips = db.query(Trip).all()
        print(f"Total trips found in database: {len(trips)}")
        
        seen_images = {}
        duplicates = []
        
        for t in trips:
            enriched = enrich_trip_response(t, db)
            trip_id = enriched.get("id")
            dest = enriched.get("destination")
            cover_img = enriched.get("cover_image")
            status = enriched.get("trip_status")
            
            print(f"ID: {trip_id:3} | Destination: '{dest:25}' | Status: '{status:10}' | Cover Image: {cover_img}")
            
            if cover_img in seen_images:
                duplicates.append((trip_id, dest, seen_images[cover_img], cover_img))
            else:
                seen_images[cover_img] = (trip_id, dest)
                
        print("\n--- DUPLICATE COVER IMAGE ANALYSIS ---")
        if duplicates:
            print(f"Found {len(duplicates)} duplicate image occurrences across total {len(trips)} trips:")
            for d in duplicates:
                print(f"  Trip {d[0]} ('{d[1]}') shares image with Trip {d[2][0]} ('{d[2][1]}'): {d[3]}")
        else:
            print("[SUCCESS] Every trip in database returns a UNIQUE or correctly resolved cover image!")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_api_trips_payload()
