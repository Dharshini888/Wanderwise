from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class PackingList(Base):
    __tablename__ = "packing_lists"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    destination = Column(String, nullable=False)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    duration_days = Column(Integer, nullable=False, default=1)
    
    season = Column(String, nullable=True)
    climate = Column(String, nullable=True)
    weather_source = Column(String, nullable=True)
    
    # Store the actual structured JSON packing list, warnings, etc.
    categories = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=True, default=list)
    missing_essentials = Column(JSON, nullable=True, default=list)
    packing_score = Column(Float, nullable=True, default=0.0)
    daily_gear = Column(JSON, nullable=True, default=list)
    generation_source = Column(String, nullable=True, default="ai")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    trip = relationship("Trip", back_populates="packing_lists")
    user = relationship("User")
