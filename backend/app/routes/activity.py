from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.activity import ActivityLog
from app.models.user import User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/activity", tags=["Activity"])

@router.get("/user/{user_id}")
def get_user_activity(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activity for the current user."""
    # Data isolation check
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this activity")
        
    activities = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id).order_by(ActivityLog.created_at.desc()).limit(20).all()
    return activities
