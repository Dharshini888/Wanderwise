from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    mood = Column(String, nullable=True)  # happy, excited, tired, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip", back_populates="journal_entries")
