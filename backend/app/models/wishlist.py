from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination = Column(String, nullable=False)
    country = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    priority = Column(String, default="someday")  # dream / soon / someday
    estimated_budget = Column(Float, default=120000.0)
    duration_days = Column(Integer, default=7)
    best_season = Column(String, default="October - March")
    travel_style = Column(String, default="Nature & Culture")
    image_url = Column(String, nullable=True)
    rating = Column(Float, default=4.8)
    ai_match_score = Column(Float, default=92.0)
    is_visited = Column(Boolean, default=False)
    is_planned = Column(Boolean, default=False)
    visa_required = Column(Boolean, default=False)
    is_international = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wishlist_items")
