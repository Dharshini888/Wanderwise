import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.recommendations import UserTravelProfile, DestinationKnowledge, RecommendationHistory
from app.services.ai_recommendation_service import AIRecommendationService

def test_ai_recommendations_suite():
    print("=== STARTING WANDERWISE v2.6 BACKEND TEST SUITE (TEST_AI_RECOMMENDATIONS.PY) ===")
    db = SessionLocal()
    try:
        # Create test users
        u1 = db.query(User).filter(User.email == "rec_u1@wanderwise.com").first()
        if not u1:
            u1 = User(email="rec_u1@wanderwise.com", name="Dharshini Travel", password="pw", travel_preference="Nature & Waterfalls")
            db.add(u1)

        db.commit()
        db.refresh(u1)

        # Create past trip for User 1
        t1 = Trip(
            user_id=u1.id,
            destination="Kerala",
            country="India",
            start_date=date.today() - date.resolution * 10,
            end_date=date.today() - date.resolution * 5,
            budget=500.0,
            status="Completed"
        )
        db.add(t1)
        db.commit()

        # --- 1. Test Seed Knowledge Base ---
        print("\n--- 1. Testing Destination Knowledge Base Seeding ---")
        AIRecommendationService.seed_destination_knowledge(db)
        dk_count = db.query(DestinationKnowledge).count()
        print(f"Destination Knowledge Base Count: {dk_count}")
        assert dk_count >= 5
        print("[SUCCESS] Destination Knowledge Base Seeded!")

        # --- 2. Test User Travel Profile Learning ---
        print("\n--- 2. Testing User Travel Profile Learning Engine ---")
        profile = AIRecommendationService.build_user_travel_profile(u1.id, db)
        print(f"User #{u1.id} Profile Favorites: {profile.favorite_categories} | Visited: {profile.visited_destinations}")
        assert profile.user_id == u1.id
        assert len(profile.favorite_categories) > 0
        print("[SUCCESS] User Travel Profile Learned!")

        # --- 3. Test 5-Factor Recommendation Scoring Engine ---
        print("\n--- 3. Testing 5-Factor Recommendation Scoring Engine ---")
        recs = AIRecommendationService.generate_personalized_recommendations(u1.id, db)
        print(f"Generated Personalized Recommendations Count: {len(recs)}")
        assert len(recs) > 0

        top_rec = recs[0]
        print(f"Top Recommended Destination: '{top_rec['destination']}' | Match Score: {top_rec['match_score']}%")
        print(f"Why Reasons: {top_rec['why_reasons']}")
        assert top_rec["match_score"] >= 50
        assert len(top_rec["why_reasons"]) > 0
        print("[SUCCESS] 5-Factor Scoring Verified!")

        # Cleanup test records
        db.delete(t1)
        db.query(UserTravelProfile).filter(UserTravelProfile.user_id == u1.id).delete()
        db.commit()

        print("\n=== ALL WANDERWISE v2.6 AI RECOMMENDATIONS BACKEND TESTS PASSED CLEANLY (100%) ===")

    finally:
        db.close()

if __name__ == "__main__":
    test_ai_recommendations_suite()
