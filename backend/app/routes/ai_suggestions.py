from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.connection import get_db
from app.models.user import User
from app.services.ai_suggestion_service import AISuggestionService
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/ai/suggestions", tags=["AI Suggestions & Proactive Hub"])

@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
def get_user_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve active user suggestions categorized by priority (high, medium, low)."""
    # Auto-generate fresh suggestions if user has 0 active items
    res = AISuggestionService.get_user_suggestions(user_id=current_user.id, db=db)
    if res.get("all_count", 0) == 0:
        res = AISuggestionService.generate_user_suggestions(user_id=current_user.id, db=db)
    return res


@router.post("/generate", response_model=Dict[str, Any])
def generate_fresh_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force re-run AI suggestion generators and return updated suggestions."""
    return AISuggestionService.generate_user_suggestions(user_id=current_user.id, db=db)


@router.post("/{suggestion_id}/complete")
def complete_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a suggestion as completed with user isolation."""
    try:
        AISuggestionService.mark_suggestion_complete(suggestion_id=suggestion_id, user_id=current_user.id, db=db)
        return {"message": "Suggestion marked as complete"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{suggestion_id}/dismiss")
def dismiss_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dismiss a suggestion with user isolation."""
    try:
        AISuggestionService.dismiss_suggestion(suggestion_id=suggestion_id, user_id=current_user.id, db=db)
        return {"message": "Suggestion dismissed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
