from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.routes.auth import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.checklist import ChecklistItem
from app.services.checklist_generator import (
    generate_checklist_for_trip,
    calculate_readiness_score,
    _to_datetime
)

router = APIRouter(prefix="/api/checklist", tags=["Checklist"])


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class ChecklistCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = "CUSTOM"
    priority: Optional[str] = "MEDIUM"
    due_date: Optional[str] = None


class ChecklistUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@router.get("/{trip_id}")
def get_trip_checklist(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all checklist items and summary readiness score for specified trip owned by authenticated user.
    Auto-generates initial checklist if none exists yet.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or access denied."
        )

    items = db.query(ChecklistItem).filter(
        ChecklistItem.trip_id == trip_id,
        ChecklistItem.user_id == current_user.id
    ).order_by(ChecklistItem.created_at.asc()).all()

    # If no items exist yet for this trip, auto-generate them on first fetch
    if not items:
        items = generate_checklist_for_trip(db, trip_id, current_user.id)

    summary = calculate_readiness_score(items)

    return {
        "trip_id": trip_id,
        "summary": summary,
        "items": [item.to_dict() for item in items]
    }


@router.post("/{trip_id}", status_code=status.HTTP_201_CREATED)
def create_custom_checklist_item(
    trip_id: int,
    payload: ChecklistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a user-defined custom checklist task for a trip.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or access denied."
        )

    due_dt = _to_datetime(payload.due_date) if payload.due_date else None

    item = ChecklistItem(
        user_id=current_user.id,
        trip_id=trip_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        category=(payload.category or "CUSTOM").upper(),
        priority=(payload.priority or "MEDIUM").upper(),
        status="PENDING",
        due_date=due_dt,
        source="USER",
        action_type="CUSTOM_TASK",
        action_target=None,
        is_auto_generated=False,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item.to_dict()


@router.patch("/{item_id}")
def update_checklist_item(
    item_id: int,
    payload: ChecklistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates status, title, description, priority, or due_date of a checklist item.
    """
    item = db.query(ChecklistItem).filter(
        ChecklistItem.id == item_id,
        ChecklistItem.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist item not found or access denied."
        )

    if payload.title is not None:
        item.title = payload.title.strip()
    if payload.description is not None:
        item.description = payload.description.strip()
    if payload.priority is not None:
        item.priority = payload.priority.upper()
    if payload.due_date is not None:
        item.due_date = _to_datetime(payload.due_date)

    if payload.status is not None:
        new_status = payload.status.upper()
        if new_status in ["PENDING", "COMPLETED", "SKIPPED"]:
            item.status = new_status
            if new_status == "COMPLETED":
                item.completed_at = datetime.now(timezone.utc)
            elif new_status == "PENDING":
                item.completed_at = None

    db.commit()
    db.refresh(item)

    return item.to_dict()


@router.delete("/{item_id}")
def delete_checklist_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a checklist item owned by user.
    """
    item = db.query(ChecklistItem).filter(
        ChecklistItem.id == item_id,
        ChecklistItem.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist item not found or access denied."
        )

    db.delete(item)
    db.commit()

    return {"message": "Checklist item deleted successfully", "id": item_id}


@router.post("/{trip_id}/generate")
def generate_checklist_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates or updates automatic checklist items for specified trip based on real DB state.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or access denied."
        )

    items = generate_checklist_for_trip(db, trip_id, current_user.id)
    summary = calculate_readiness_score(items)

    return {
        "message": "Checklist generated successfully",
        "trip_id": trip_id,
        "summary": summary,
        "items": [item.to_dict() for item in items]
    }
