from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any

from app.database.connection import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.services.ai_chat_service import AIChatService
from app.routes.auth import get_current_user, get_current_user

router = APIRouter(prefix="/api/chat", tags=["AI Travel Companion Chat"])

class SessionCreateRequest(BaseModel):
    trip_id: Optional[int] = None
    title: Optional[str] = None

class MessageSendRequest(BaseModel):
    session_id: Optional[int] = None
    message: str


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_chat_session(
    data: SessionCreateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session for current user."""
    trip_id = data.trip_id if data else None
    title = data.title if data else None
    session = AIChatService.create_session(user_id=current_user.id, trip_id=trip_id, title=title, db=db)
    return {
        "id": session.id,
        "trip_id": session.trip_id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None
    }


@router.get("/sessions")
def get_user_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve user chat sessions sorted by recent activity with user isolation."""
    return AIChatService.get_user_sessions(user_id=current_user.id, db=db)


@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session with strict user isolation."""
    try:
        AIChatService.delete_session(session_id=session_id, user_id=current_user.id, db=db)
        return {"message": "Session deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch message history for a specific chat session with user isolation."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found or unauthorized")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "actions": m.actions,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]


@router.post("/message")
def send_chat_message(
    data: MessageSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send user message, retrieve context, call AI model, detect actions, and persist conversation."""
    session_id = data.session_id

    # Auto-create session if session_id is omitted or not provided
    if not session_id:
        session = AIChatService.create_session(user_id=current_user.id, title=data.message[:30], db=db)
        session_id = session.id

    try:
        res = AIChatService.process_user_message(
            session_id=session_id,
            message_text=data.message,
            user_id=current_user.id,
            db=db
        )
        return {
            "session_id": res["session_id"],
            "reply": res["reply"],
            "response": res["reply"],
            "actions": res["actions"]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))