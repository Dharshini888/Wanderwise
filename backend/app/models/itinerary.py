from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class ItineraryDay(Base):
    __tablename__ = "itinerary_days"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    title = Column(String, nullable=True)
    theme_note = Column(String, nullable=True)

    trip = relationship("Trip", back_populates="itinerary_days")
    activities = relationship("ItineraryActivity", back_populates="day", cascade="all, delete-orphan", order_by="ItineraryActivity.order_index")


class ItineraryActivity(Base):
    __tablename__ = "itinerary_activities"

    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("itinerary_days.id", ondelete="CASCADE"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="SET NULL"), nullable=True)
    
    time_slot = Column(String, default="morning")  # morning, afternoon, evening, night, custom
    start_time = Column(String, nullable=True)     # e.g. "08:30"
    end_time = Column(String, nullable=True)       # e.g. "10:00"
    duration_minutes = Column(Integer, default=90)
    order_index = Column(Integer, default=0)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    estimated_duration = Column(String, default="1-2 hours")
    ticket_price = Column(Float, default=0.0)
    
    transport_mode = Column(String, default="walking")  # walking, metro, taxi, bus, train
    transport_duration = Column(String, nullable=True)
    weather_suitability = Column(String, default="all-weather")  # indoor, outdoor, all-weather
    crowd_level = Column(String, default="moderate")             # low, moderate, high
    
    ai_reason = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.95)
    is_locked = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Rich AI Activity Metadata (tips, nearby places, rain backup, photo rating)
    activity_metadata = Column(JSON, nullable=True)

    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    day = relationship("ItineraryDay", back_populates="activities")
    place = relationship("Place", back_populates="activities")
