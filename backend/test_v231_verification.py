import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.cover_image_service import CoverImageService, CURATED_DESTINATION_IMAGES, DETERMINISTIC_FALLBACK_POOL

def test_cover_image_resolution():
    print("=== STARTING WANDERWISE v2.3.1 COVER IMAGE RESOLUTION TEST ===")

    test_destinations = [
        "Bali",
        "Tokyo",
        "Paris",
        "Varkala",
        "London",
        "New York",
        "NYC",
        "Bombay",
        "Hawaii",
        "Seoul",
        "Zurich",
        "Reykjavik",
        "Bora Bora"
    ]

    resolved_urls = {}

    for dest in test_destinations:
        url = CoverImageService.get_cover_image(dest)
        resolved_urls[dest] = url
        print(f"Destination: '{dest:12}' -> Resolved Cover Image: '{url}'")

    # Verification Checks:
    # 1. Bali, Tokyo, Paris, Varkala, London, New York should match curated
    assert resolved_urls["Bali"] == CURATED_DESTINATION_IMAGES["bali"]
    assert resolved_urls["Tokyo"] == CURATED_DESTINATION_IMAGES["tokyo"]
    assert resolved_urls["Paris"] == CURATED_DESTINATION_IMAGES["paris"]
    assert resolved_urls["Varkala"] == CURATED_DESTINATION_IMAGES["varkala"]
    assert resolved_urls["London"] == CURATED_DESTINATION_IMAGES["london"]
    assert resolved_urls["New York"] == CURATED_DESTINATION_IMAGES["new york"]

    # 2. NYC alias should resolve to New York image
    assert resolved_urls["NYC"] == CURATED_DESTINATION_IMAGES["new york"]

    # 3. Bombay alias should resolve to Mumbai image
    assert resolved_urls["Bombay"] == CURATED_DESTINATION_IMAGES["mumbai"]

    # 4. Hawaii should resolve to Hawaii image
    assert resolved_urls["Hawaii"] == CURATED_DESTINATION_IMAGES["hawaii"]

    # 5. Seoul should resolve to Seoul image
    assert resolved_urls["Seoul"] == CURATED_DESTINATION_IMAGES["seoul"]

    # 6. Unmapped destinations (Zurich, Reykjavik, Bora Bora) should resolve to distinct fallback images
    zurich_url = resolved_urls["Zurich"]
    reykjavik_url = resolved_urls["Reykjavik"]
    borabora_url = resolved_urls["Bora Bora"]

    assert zurich_url in DETERMINISTIC_FALLBACK_POOL
    assert reykjavik_url in DETERMINISTIC_FALLBACK_POOL
    assert borabora_url in DETERMINISTIC_FALLBACK_POOL

    # Verify Zurich, Reykjavik, and Bora Bora get DIFFERENT fallback URLs
    assert zurich_url != reykjavik_url, f"Zurich and Reykjavik share duplicate fallback: {zurich_url}"
    assert reykjavik_url != borabora_url, f"Reykjavik and Bora Bora share duplicate fallback: {reykjavik_url}"
    assert zurich_url != borabora_url, f"Zurich and Bora Bora share duplicate fallback: {zurich_url}"

    print("\n[SUCCESS] All Cover Image Resolution & Alias Checks Passed 100%!")

if __name__ == "__main__":
    test_cover_image_resolution()
