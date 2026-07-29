# TODO Phase 2: Automatic event progression logger and push notification triggers.
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class TripTimeline(Base):
    __tablename__ = "trip_timeline"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    
    event_type = Column(String, nullable=False)  # booking_created, flight_confirmed, visa_uploaded, trip_started, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(Text, nullable=True)

    trip = relationship("Trip", back_populates="timeline_events")
