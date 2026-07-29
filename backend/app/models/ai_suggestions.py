from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True)

    type = Column(String(50), nullable=False, index=True)  # weather, budget, itinerary, destination, packing, experience, alert
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    priority = Column(String(20), default="medium")       # high, medium, low
    priority_score = Column(Integer, default=50)         # 0-100 scoring scale

    metadata_json = Column(JSON, nullable=True)          # actions, why_reasons, suggested_changes, dest_info
    status = Column(String(20), default="active", index=True) # active, completed, dismissed

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    user = relationship("User")
    trip = relationship("Trip")

    __table_args__ = (
        Index("idx_suggestion_user_status", "user_id", "status"),
        Index("idx_suggestion_type", "type"),
        Index("idx_suggestion_user_trip", "user_id", "trip_id"),
    )
