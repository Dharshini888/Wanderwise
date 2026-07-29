import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.trip import Trip
from app.services.trip_service import enrich_trip_response
from app.services.cover_image_service import CoverImageService, CURATED_DESTINATION_IMAGES, DETERMINISTIC_FALLBACK_POOL

def test_full_end_to_end_verification():
    print("=== STARTING FULL END-TO-END BACKEND & API VERIFICATION ===")
    
    # 1. Test Cover Image Resolver Unit Logic
    print("\n--- 1. Testing CoverImageService Unit Resolution ---")
    destinations = ["Bali", "Tokyo", "Paris", "Varkala", "London", "New York", "NYC", "Bombay", "Hawaii", "Seoul", "Zurich", "Reykjavik", "Bora Bora"]
    urls = {}
    for d in destinations:
        url = CoverImageService.get_cover_image(d)
        urls[d] = url
        print(f"Destination: '{d:12}' -> Resolved Cover Image: '{url}'")

    assert urls["Bali"] == CURATED_DESTINATION_IMAGES["bali"]
    assert urls["Tokyo"] == CURATED_DESTINATION_IMAGES["tokyo"]
    assert urls["Paris"] == CURATED_DESTINATION_IMAGES["paris"]
    assert urls["Varkala"] == CURATED_DESTINATION_IMAGES["varkala"]
    assert urls["London"] == CURATED_DESTINATION_IMAGES["london"]
    assert urls["New York"] == CURATED_DESTINATION_IMAGES["new york"]
    assert urls["NYC"] == CURATED_DESTINATION_IMAGES["new york"]
    assert urls["Bombay"] == CURATED_DESTINATION_IMAGES["mumbai"]
    assert urls["Hawaii"] == CURATED_DESTINATION_IMAGES["hawaii"]
    assert urls["Seoul"] == CURATED_DESTINATION_IMAGES["seoul"]
    
    # Unmapped fallback uniqueness
    z_url = urls["Zurich"]
    r_url = urls["Reykjavik"]
    b_url = urls["Bora Bora"]
    assert z_url != r_url and r_url != b_url and z_url != b_url, "Unmapped fallbacks must be distinct"
    print("[SUCCESS] Unit Cover Image Resolution verified!")

    # 2. Test API Payload Field Contracts
    print("\n--- 2. Testing API Payload Fields on Database Records ---")
    db = SessionLocal()
    try:
        trips = db.query(Trip).all()
        print(f"Found {len(trips)} trips in DB.")
        for t in trips[:10]:
            enriched = enrich_trip_response(t, db)
            assert "id" in enriched, "API payload missing 'id'"
            assert "destination" in enriched, "API payload missing 'destination'"
            assert "cover_image" in enriched, "API payload missing 'cover_image'"
            assert enriched["cover_image"] is not None, "cover_image should not be null"
            assert enriched["cover_image"].startswith("http"), "cover_image must be a valid URL"
            print(f"Verified Trip #{enriched['id']:3} ({enriched['destination']}): {enriched['cover_image']}")
        print("[SUCCESS] API Payload Field Contracts verified!")
    finally:
        db.close()

    print("\n=== ALL END-TO-END VERIFICATION CHECKS PASSED CLEANLY (100%) ===")

if __name__ == "__main__":
    test_full_end_to_end_verification()
