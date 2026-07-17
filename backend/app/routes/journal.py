from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.connection import get_db
from app.models.journal import JournalEntry
from app.models.trip import Trip
from app.services.ai_service import generate_trip_memory

router = APIRouter(prefix="/api/journal", tags=["Journal"])


class EntryCreate(BaseModel):
    title: str = ""
    content: str
    mood: str = "happy"


@router.get("/{trip_id}")
def get_entries(trip_id: int, db: Session = Depends(get_db)):
    entries = db.query(JournalEntry).filter(
        JournalEntry.trip_id == trip_id
    ).order_by(JournalEntry.created_at.asc()).all()
    return entries


@router.post("/{trip_id}")
def add_entry(trip_id: int, data: EntryCreate, db: Session = Depends(get_db)):
    entry = JournalEntry(
        trip_id=trip_id,
        title=data.title,
        content=data.content,
        mood=data.mood,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{trip_id}/{entry_id}")
def delete_entry(trip_id: int, entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.trip_id == trip_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"message": "Deleted"}


@router.post("/{trip_id}/memory")
def generate_memory(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    entries = db.query(JournalEntry).filter(JournalEntry.trip_id == trip_id).all()
    entries_list = [{"title": e.title or "", "content": e.content} for e in entries]

    # Get total expenses
    from app.models.expense import Expense
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    total_spent = sum(e.amount for e in expenses)

    memory = generate_trip_memory(
        destination=trip.destination,
        start_date=str(trip.start_date),
        end_date=str(trip.end_date),
        journal_entries=entries_list,
        total_spent=total_spent,
    )
    return {"memory": memory}
