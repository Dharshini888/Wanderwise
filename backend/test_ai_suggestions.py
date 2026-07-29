import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense
from app.models.ai_suggestions import AISuggestion
from app.services.ai_suggestion_service import AISuggestionService

def test_ai_suggestions_suite():
    print("=== STARTING WANDERWISE v2.6.1 BACKEND TEST SUITE (TEST_AI_SUGGESTIONS.PY) ===")
    db = SessionLocal()
    try:
        # Create test users
        u1 = db.query(User).filter(User.email == "sug_u1@wanderwise.com").first()
        if not u1:
            u1 = User(email="sug_u1@wanderwise.com", name="Dharshini Suggestions", password="pw", travel_preference="Beach & Food")
            db.add(u1)

        u2 = db.query(User).filter(User.email == "sug_u2@wanderwise.com").first()
        if not u2:
            u2 = User(email="sug_u2@wanderwise.com", name="User Two", password="pw")
            db.add(u2)

        db.commit()
        db.refresh(u1)
        db.refresh(u2)

        # Create high budget usage trip for User 1
        trip = Trip(
            user_id=u1.id,
            destination="Bali",
            country="Indonesia",
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=4),
            budget=1000.0,
            status="Active"
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        # Add heavy expense to trigger budget warning (>75%)
        exp = Expense(
            trip_id=trip.id,
            title="Bali Resort & Seafood",
            amount=800.0,
            currency="USD",
            expense_date=date.today()
        )
        db.add(exp)
        db.commit()

        # --- 1. Test Suggestion Generation & Priority Scoring ---
        print("\n--- 1. Testing Suggestion Generation & Priority Scoring ---")
        res = AISuggestionService.generate_user_suggestions(u1.id, db)
        print(f"Generated Suggestions Count: High={len(res['high'])}, Medium={len(res['medium'])}, Low={len(res['low'])}")
        assert res["all_count"] > 0

        # Check High Priority Budget Warning
        high_items = res["high"]
        assert len(high_items) > 0
        budget_warn = high_items[0]
        assert budget_warn["priority"] == "high"
        assert budget_warn["priority_score"] >= 80
        safe_title = budget_warn['title'].encode('ascii', 'ignore').decode('ascii')
        print(f"[SUCCESS] High Priority Suggestion Generated: '{safe_title}' (Score: {budget_warn['priority_score']})")

        # --- 2. Test AI Explanation Layer ("Why am I seeing this?") ---
        print("\n--- 2. Testing AI Explanation Layer Metadata ---")
        why_reasons = budget_warn["metadata"].get("why_reasons", [])
        print(f"Explanation Reasons: {why_reasons}")
        assert len(why_reasons) > 0
        print("[SUCCESS] Explanation Layer Reasons Verified!")

        # --- 3. Test Duplicate Prevention ---
        print("\n--- 3. Testing Duplicate Prevention ---")
        count_before = db.query(AISuggestion).filter(AISuggestion.user_id == u1.id).count()
        AISuggestionService.generate_user_suggestions(u1.id, db)
        count_after = db.query(AISuggestion).filter(AISuggestion.user_id == u1.id).count()
        assert count_before == count_after
        print(f"[SUCCESS] Duplicate Prevention Verified! (Count unchanged at {count_after})")

        # --- 4. Test User Isolation Security ---
        print("\n--- 4. Testing User Isolation Security ---")
        u2_suggestions = AISuggestionService.get_user_suggestions(u2.id, db)
        print(f"User #2 Active Suggestions Count: {u2_suggestions['all_count']}")
        assert u2_suggestions["all_count"] == 0

        try:
            AISuggestionService.dismiss_suggestion(budget_warn["id"], u2.id, db)
            assert False, "User 2 must NOT dismiss User 1's suggestion"
        except ValueError:
            print("[SUCCESS] User isolation blocked unauthorized suggestion dismissal!")

        # --- 5. Test Complete & Dismiss Actions ---
        print("\n--- 5. Testing Complete & Dismiss Actions ---")
        sug_id = budget_warn["id"]
        AISuggestionService.mark_suggestion_complete(sug_id, u1.id, db)
        print(f"[SUCCESS] Suggestion #{sug_id} marked complete.")

        res_after = AISuggestionService.get_user_suggestions(u1.id, db)
        active_ids = [s["id"] for group in [res_after["high"], res_after["medium"], res_after["low"]] for s in group]
        assert sug_id not in active_ids
        print("[SUCCESS] Completed suggestion removed from active list!")

        # Cleanup test records
        db.delete(exp)
        db.delete(trip)
        db.query(AISuggestion).filter(AISuggestion.user_id.in_([u1.id, u2.id])).delete()
        db.commit()

        print("\n=== ALL WANDERWISE v2.6.1 AI SUGGESTIONS BACKEND TESTS PASSED CLEANLY (100%) ===")

    finally:
        db.close()

if __name__ == "__main__":
    test_ai_suggestions_suite()
