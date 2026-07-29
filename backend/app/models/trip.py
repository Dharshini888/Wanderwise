from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=True)
    destination = Column(String, nullable=False)
    country = Column(String, nullable=True)
    origin_city = Column(String, default="Coimbatore")
    origin_airport = Column(String, nullable=True)
    destination_airport = Column(String, nullable=True)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    travel_type = Column(String, nullable=True)
    travel_style = Column(String, default="solo")  # solo, couple, friends, family, business, backpacking, luxury, road_trip
    transportation = Column(String, default="flight")  # flight, train, bus, car, rental
    accommodation_preference = Column(String, default="hotel")  # hotel, hostel, resort, airbnb
    interests = Column(String, nullable=True)
    travel_companion = Column(String, nullable=True)
    group_size = Column(Integer, default=1)
    
    visibility = Column(String, default="private")  # private, shared, public
    notes = Column(Text, nullable=True)
    itinerary = Column(Text, nullable=True)  # Legacy text field preserved for backward compatibility
    
    # 8 Travel States: Draft, Planning, Booked, Upcoming, In Progress, Completed, Cancelled, Archived
    status = Column(String, default="Upcoming")
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    color_theme = Column(String, default="blue")
    image_url = Column(String, nullable=True)
    share_token = Column(String, unique=True, nullable=True)
    
    # Extended 14-Step Wizard JSON preferences
    trip_preferences = Column(JSON, nullable=True)

    # Sustainability & Mood
    carbon_footprint = Column(Float, default=0.0)
    sustainability_score = Column(Float, default=0.0)
    current_mood = Column(String, nullable=True)
    is_group_trip = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_opened_at = Column(DateTime(timezone=True), nullable=True)


    # Relationships
    user = relationship("User", back_populates="trips")
    expenses = relationship("Expense", back_populates="trip")
    budget_obj = relationship("Budget", back_populates="trip", uselist=False, cascade="all, delete")
    journal_entries = relationship("JournalEntry", back_populates="trip")

    itinerary_days = relationship("ItineraryDay", back_populates="trip", cascade="all, delete-orphan", order_by="ItineraryDay.day_number")
    bookings = relationship("TripBooking", back_populates="trip", cascade="all, delete-orphan")
    timeline_events = relationship("TripTimeline", back_populates="trip", cascade="all, delete-orphan")
    health_info = relationship("TripHealth", back_populates="trip", uselist=False, cascade="all, delete-orphan")
    ai_context = relationship("TripAIContext", back_populates="trip", uselist=False, cascade="all, delete-orphan")

