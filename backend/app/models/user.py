from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    travel_preference = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # v2 Features
    dietary_preferences = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    accessibility_needs = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    passport_expiry = Column(DateTime(timezone=True), nullable=True)

    trips = relationship("Trip", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user")
