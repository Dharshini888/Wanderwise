from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String, nullable=False, default="CUSTOM")  # DOCUMENTS, BOOKINGS, MONEY, PACKING, ITINERARY, WEATHER, TRANSIT, SAFETY, CUSTOM
    priority = Column(String, nullable=False, default="MEDIUM")   # LOW, MEDIUM, HIGH, URGENT
    status = Column(String, nullable=False, default="PENDING")     # PENDING, COMPLETED, SKIPPED
    due_date = Column(DateTime(timezone=True), nullable=True)

    source = Column(String, nullable=False, default="SYSTEM")     # SYSTEM, DOCUMENTS, TRIP, PACKING, BUDGET, TRANSIT, WEATHER, USER
    action_type = Column(String, nullable=True)                  # e.g., UPLOAD_PASSPORT, CREATE_PACKING
    action_target = Column(String, nullable=True)                # e.g., /documents, /packing, /budget, /transit
    is_auto_generated = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    trip = relationship("Trip", back_populates="checklist_items")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trip_id": self.trip_id,
            "title": self.title,
            "description": self.description or "",
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "source": self.source,
            "action_type": self.action_type,
            "action_target": self.action_target,
            "is_auto_generated": self.is_auto_generated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
