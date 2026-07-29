# TODO Phase 2: LLM long-term travel memory, recommendation vectors, and cross-trip context retrieval.
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class TripAIContext(Base):
    __tablename__ = "trip_ai_context"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    season = Column(String, nullable=True)
    weather_summary = Column(String, nullable=True)
    festival_info = Column(Text, nullable=True)
    is_peak_season = Column(String, nullable=True)
    crowd_prediction = Column(String, nullable=True)
    local_events = Column(Text, nullable=True)  # JSON string
    currency_rate = Column(Float, nullable=True)
    safety_score = Column(Float, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    trip = relationship("Trip", back_populates="ai_context")


class TripAIMemory(Base):
    __tablename__ = "trip_ai_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    
    memory_key = Column(String, nullable=False)  # favorite_food, avoids_trekking, budget_conscious, etc.
    memory_value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
