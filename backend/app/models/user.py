from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    auth_provider = Column(String, default="local", nullable=False)
    phone_number = Column(String, nullable=True)
    travel_preference = Column(String, nullable=True)
    role = Column(String, default="USER", nullable=False)
    profile_completed = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # v2 Features
    dietary_preferences = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    accessibility_needs = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    passport_expiry = Column(DateTime(timezone=True), nullable=True)

    # User Preferences
    preferred_budget = Column(String, nullable=True)
    currency = Column(String, default="USD")
    travel_styles = Column(String, nullable=True)
    preferred_climate = Column(String, nullable=True)
    preferred_activities = Column(String, nullable=True)
    languages = Column(String, nullable=True)

    trips = relationship("Trip", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user")
