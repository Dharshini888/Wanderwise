from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    travel_type = Column(String, nullable=True)
    travel_style = Column(String, default="solo")
    group_size = Column(Integer, default=1)
    interests = Column(String, nullable=True)
    itinerary = Column(Text, nullable=True)
    
    # v2 Features
    carbon_footprint = Column(Float, default=0.0)
    sustainability_score = Column(Float, default=0.0)
    current_mood = Column(String, nullable=True)
    is_group_trip = Column(Boolean, default=False)

    user = relationship("User", back_populates="trips")
    expenses = relationship("Expense", back_populates="trip")
    journal_entries = relationship("JournalEntry", back_populates="trip")
