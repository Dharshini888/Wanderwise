from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.connection import get_db
from app.models.wishlist import WishlistItem
from app.services.ai_service import personalized_destinations
import json

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


class WishlistCreate(BaseModel):
    user_id: int
    destination: str
    country: str = ""
    notes: str = ""
    priority: str = "someday"


@router.get("/{user_id}")
def get_wishlist(user_id: int, db: Session = Depends(get_db)):
    items = db.query(WishlistItem).filter(
        WishlistItem.user_id == user_id
    ).order_by(WishlistItem.created_at.desc()).all()
    return items


@router.post("/add")
def add_to_wishlist(data: WishlistCreate, db: Session = Depends(get_db)):
    item = WishlistItem(
        user_id=data.user_id,
        destination=data.destination,
        country=data.country,
        notes=data.notes,
        priority=data.priority,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def remove_from_wishlist(item_id: int, db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Removed from wishlist"}


@router.patch("/{item_id}/priority")
def update_priority(item_id: int, priority: str, db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.priority = priority
    db.commit()
    return item

@router.get("/recommendations/{user_id}")
def get_wishlist_recommendations(user_id: int, db: Session = Depends(get_db)):
    items = db.query(WishlistItem).filter(WishlistItem.user_id == user_id).all()
    past_destinations = [item.destination for item in items]
    
    try:
        raw_recs = personalized_destinations(past_destinations)
        
        # Clean potential markdown
        text = raw_recs.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
                
        return json.loads(text.strip())
    except Exception as e:
        return [{"destination": "Paris, France", "reason": "A classic destination for any traveler.", "vibe": "Historic"}]

