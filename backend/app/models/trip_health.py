# TODO Phase 2: Safety & Health automated visa validation, document scanning, and emergency response.
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class TripHealth(Base):
    __tablename__ = "trip_health"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    visa_status = Column(String, default="not_required")  # not_required, pending, approved, exempt
    passport_uploaded = Column(Boolean, default=False)
    insurance_uploaded = Column(Boolean, default=False)
    vaccination_status = Column(String, nullable=True)
    
    emergency_contacts = Column(Text, nullable=True)  # JSON string of contacts
    medical_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    trip = relationship("Trip", back_populates="health_info")
