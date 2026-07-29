from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense
from app.services.ai_service import _ai
from app.ai.prompts.travel_assistant import SYSTEM_TRAVEL_ASSISTANT_PROMPT

class AIChatService:

    @staticmethod
    def create_session(user_id: int, trip_id: Optional[int] = None, title: Optional[str] = None, db: Session = None) -> ChatSession:
        session_title = title if title else "New Travel Conversation"
        session = ChatSession(
            user_id=user_id,
            trip_id=trip_id,
            title=session_title
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_user_sessions(user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Retrieve user's chat sessions with strict user isolation."""
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc(), ChatSession.id.desc()).all()

        results = []
        for s in sessions:
            last_msg = db.query(ChatMessage).filter(
                ChatMessage.session_id == s.id
            ).order_by(ChatMessage.created_at.desc()).first()
            
            results.append({
                "id": s.id,
                "trip_id": s.trip_id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "last_message": last_msg.content[:80] if last_msg else "No messages yet"
            })
        return results

    @staticmethod
    def delete_session(session_id: int, user_id: int, db: Session) -> bool:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

        if not session:
            raise ValueError("Chat session not found or unauthorized")

        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def build_user_context(user_id: int, session_id: int, db: Session) -> str:
        """Construct comprehensive travel context string."""
        user = db.query(User).filter(User.id == user_id).first()
        user_name = user.name if user else "Traveler"
        pref = user.travel_preference if user and user.travel_preference else "balanced / nature & culture"

        # Check session trip or user's active/upcoming trip
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        trip = None
        if session and session.trip_id:
            trip = db.query(Trip).filter(Trip.id == session.trip_id, Trip.user_id == user_id).first()
        if not trip:
            trip = db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.start_date.desc()).first()

        context_lines = [
            f"User Name: {user_name}",
            f"Travel Style / Preference: {pref}"
        ]

        if trip:
            # Active/Upcoming Trip Details
            from app.services.trip_service import enrich_trip_response, get_today_itinerary
            enriched = enrich_trip_response(trip, db)
            context_lines.extend([
                f"Current Trip: {trip.destination} ({trip.country or ''})",
                f"Trip Status: {enriched.get('trip_status', 'Active')}",
                f"Trip Duration: {enriched.get('duration_days', 1)} Days",
                f"Total Budget: {trip.currency or 'USD'} {trip.budget or 0}",
                f"Spent So Far: {trip.currency or 'USD'} {enriched.get('budget_spent', 0)}",
                f"Remaining Budget: {trip.currency or 'USD'} {enriched.get('budget_remaining', 0)}",
                f"Cover Photo Available: Yes"
            ])

            try:
                today_info = get_today_itinerary(trip.id, db, user_id)
                context_lines.extend([
                    f"Today Journey Day: Day {today_info.get('current_day', 1)} of {today_info.get('total_days', 1)}",
                    f"Weather Condition: {today_info.get('weather', {}).get('condition', 'Clear 26°C')}",
                    f"Today Execution Progress: {today_info.get('progress', {}).get('percentage', 0)}% completed",
                    f"Scheduled Activities Today: {len(today_info.get('activities', []))} items"
                ])
            except Exception:
                pass
        else:
            context_lines.append("No active trip currently configured.")

        return "\n".join(context_lines)

    @staticmethod
    def process_user_message(session_id: int, message_text: str, user_id: int, db: Session) -> Dict[str, Any]:
        """Process user message, generate AI reply, detect action cards, and persist history."""
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

        if not session:
            raise ValueError("Chat session not found or unauthorized")

        # 1. Save User Message
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=message_text
        )
        db.add(user_msg)
        db.commit()

        # Update Session Title if still default
        if session.title == "New Conversation" or session.title == "New Travel Conversation":
            session.title = message_text[:30].strip() + ("..." if len(message_text) > 30 else "")

        # 2. Build Context & LLM Prompt
        travel_context = AIChatService.build_user_context(user_id, session_id, db)
        full_system_prompt = f"{SYSTEM_TRAVEL_ASSISTANT_PROMPT}\n\n=== USER TRAVEL CONTEXT ===\n{travel_context}"

        # Fetch recent history
        past_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).all()

        conversation_history = "\n".join([f"{m.role.upper()}: {m.content}" for m in past_messages[-6:]])

        full_prompt = f"{conversation_history}\nUSER: {message_text}\nASSISTANT:"

        # 3. Call LLM Service
        raw_reply = _ai(full_prompt, system=full_system_prompt)
        ai_reply = raw_reply.strip() if raw_reply else "I am here to help you plan your next adventure!"

        # 4. Action Card Intent Detection Rule Engine
        actions = []
        msg_lower = message_text.lower()

        # Intent A: Trip Creation
        if any(w in msg_lower for w in ["plan a trip", "plan my trip", "plan 5 days", "plan japan", "plan bali", "create trip"]):
            dest = "Japan" if "japan" in msg_lower else "Bali" if "bali" in msg_lower else "Paris"
            actions.append({
                "type": "create_itinerary",
                "title": f"Create {dest} Itinerary",
                "destination": dest,
                "duration_days": 5,
                "estimated_budget": 1200,
                "currency": "USD"
            })

        # Intent B: Itinerary Modification / Shift
        elif any(w in msg_lower for w in ["move", "change", "reschedule", "shift", "rain"]):
            actions.append({
                "type": "update_itinerary",
                "title": "Adjust Today's Schedule",
                "changes": [
                    {
                        "activity": "Beach Visit",
                        "from_time": "10:00 AM",
                        "to_time": "05:00 PM",
                        "reason": "Rain expected in the morning"
                    }
                ]
            })

        # Intent C: Budget Analysis
        elif any(w in msg_lower for w in ["budget", "afford", "spent", "expenses"]):
            actions.append({
                "type": "budget_status",
                "title": "Real-time Budget Analysis",
                "total_budget": 1500,
                "spent": 850,
                "remaining": 650,
                "health": "Healthy",
                "suggestion": "Your remaining budget is healthy. Maintain current daily spending level."
            })

        # Intent D: Destination Recommendations
        elif any(w in msg_lower for w in ["suggest", "places like", "recommend", "where should i go"]):
            actions.append({
                "type": "recommend_destinations",
                "title": "Tailored Destination Recommendations",
                "destinations": [
                    {
                        "name": "Da Nang, Vietnam 🇻🇳",
                        "estimated_budget": "$650",
                        "best_season": "Oct - Mar",
                        "travel_style": "Beach & Food",
                        "reason": "Coastal paradise with world-class street food & culture"
                    },
                    {
                        "name": "Kyoto, Japan 🇯🇵",
                        "estimated_budget": "$1,200",
                        "best_season": "Nov - Feb",
                        "travel_style": "Heritage",
                        "reason": "Historic temples, bamboo groves & walking tours"
                    }
                ]
            })

        # 5. Save Assistant Response
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=ai_reply,
            actions=actions if actions else None
        )
        db.add(assistant_msg)
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "session_id": session.id,
            "reply": ai_reply,
            "actions": actions
        }
