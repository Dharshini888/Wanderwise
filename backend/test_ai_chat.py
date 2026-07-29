import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense
from app.models.chat import ChatSession, ChatMessage
from app.services.ai_chat_service import AIChatService

def test_ai_chat_suite():
    print("=== STARTING WANDERWISE v2.5 BACKEND TEST SUITE (TEST_AI_CHAT.PY) ===")
    db = SessionLocal()
    try:
        # Create test users
        u1 = db.query(User).filter(User.email == "chat_u1@wanderwise.com").first()
        if not u1:
            u1 = User(email="chat_u1@wanderwise.com", name="Dharshini Chat", password="pw", travel_preference="Adventure & Beach")
            db.add(u1)

        u2 = db.query(User).filter(User.email == "chat_u2@wanderwise.com").first()
        if not u2:
            u2 = User(email="chat_u2@wanderwise.com", name="Other User", password="pw")
            db.add(u2)

        db.commit()
        db.refresh(u1)
        db.refresh(u2)

        # Create active trip & expense for User 1
        trip = Trip(
            user_id=u1.id,
            destination="Tokyo",
            country="Japan",
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            budget=2000.0,
            status="Active"
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        exp = Expense(
            trip_id=trip.id,
            title="Tokyo Ramen",
            amount=50.0,
            currency="USD",
            expense_date=date.today()
        )
        db.add(exp)
        db.commit()

        # --- 1. Test Session Creation ---
        print("\n--- 1. Testing Session Creation ---")
        sess1 = AIChatService.create_session(user_id=u1.id, trip_id=trip.id, title="Tokyo Chat Session", db=db)
        print(f"Session Created ID #{sess1.id} for User #{u1.id}: '{sess1.title}'")
        assert sess1.id is not None
        assert sess1.user_id == u1.id

        # --- 2. Test User Context Building (Trip & Expense Injection) ---
        print("\n--- 2. Testing Context Generation (Trip & Expense Context) ---")
        ctx = AIChatService.build_user_context(user_id=u1.id, session_id=sess1.id, db=db)
        print(f"Generated Context Snippet:\n{ctx}")
        assert "Tokyo" in ctx
        assert "Remaining Budget" in ctx
        print("[SUCCESS] Context Generation Verified!")

        # --- 3. Test Message Processing & Action Card Generation ---
        print("\n--- 3. Testing Message Processing & Action Card Generation ---")
        # Test Intent A: Trip Creation Action Card
        res_trip = AIChatService.process_user_message(sess1.id, "Plan my trip to Bali for 5 days", u1.id, db)
        print(f"User Query: 'Plan my trip to Bali for 5 days'")
        print(f"AI Reply: '{res_trip['reply'][:80]}...'")
        print(f"Generated Actions: {res_trip['actions']}")
        assert len(res_trip["actions"]) > 0
        assert res_trip["actions"][0]["type"] == "create_itinerary"
        print("[SUCCESS] Create Trip Action Card Generated!")

        # Test Intent B: Budget Analysis Action Card
        res_budget = AIChatService.process_user_message(sess1.id, "Can I afford my current expenses and budget?", u1.id, db)
        assert len(res_budget["actions"]) > 0
        assert res_budget["actions"][0]["type"] == "budget_status"
        print("[SUCCESS] Budget Analysis Action Card Generated!")

        # Test Intent C: Destination Recommendations Action Card
        res_dest = AIChatService.process_user_message(sess1.id, "Suggest places like Tokyo for my next vacation", u1.id, db)
        assert len(res_dest["actions"]) > 0
        assert res_dest["actions"][0]["type"] == "recommend_destinations"
        print("[SUCCESS] Destination Recommendations Action Card Generated!")

        # --- 4. Test User Isolation Security ---
        print("\n--- 4. Testing User Isolation Security ---")
        try:
            AIChatService.process_user_message(sess1.id, "Malicious attempt", u2.id, db)
            assert False, "User 2 must NOT process messages in User 1's chat session"
        except ValueError:
            print("[SUCCESS] User isolation blocked unauthorized message processing!")

        try:
            AIChatService.delete_session(sess1.id, u2.id, db)
            assert False, "User 2 must NOT delete User 1's chat session"
        except ValueError:
            print("[SUCCESS] User isolation blocked unauthorized session deletion!")

        # --- 5. Test Session Listing & Deletion ---
        print("\n--- 5. Testing Session Listing & Deletion ---")
        sessions_u1 = AIChatService.get_user_sessions(u1.id, db)
        assert len(sessions_u1) >= 1
        print(f"User #1 Sessions Count: {len(sessions_u1)}")

        AIChatService.delete_session(sess1.id, u1.id, db)
        print(f"[SUCCESS] Session #{sess1.id} deleted successfully by owner.")

        # Cleanup test trip & expense
        db.delete(exp)
        db.delete(trip)
        db.commit()

        print("\n=== ALL WANDERWISE v2.5 AI CHAT BACKEND TESTS PASSED CLEANLY (100%) ===")

    finally:
        db.close()

if __name__ == "__main__":
    test_ai_chat_suite()
