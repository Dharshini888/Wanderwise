from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class UserTravelProfile(Base):
    __tablename__ = "user_travel_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Interest Scores (0-100 scale)
    nature_score = Column(Integer, default=70)
    adventure_score = Column(Integer, default=65)
    culture_score = Column(Integer, default=60)
    food_score = Column(Integer, default=75)
    beach_score = Column(Integer, default=50)
    history_score = Column(Integer, default=55)
    nightlife_score = Column(Integer, default=40)
    shopping_score = Column(Integer, default=45)

    # Travel Style Scores (0-100 scale)
    solo_score = Column(Integer, default=60)
    family_score = Column(Integer, default=40)
    friends_score = Column(Integer, default=50)
    luxury_score = Column(Integer, default=40)
    budget_score = Column(Integer, default=80)

    # Behavioral Intelligence
    preferred_styles = Column(JSON, nullable=True)        # ["Nature", "Photography", "Adventure"]
    favorite_categories = Column(JSON, nullable=True)     # ["Beaches", "Waterfalls", "Museums"]
    visited_destinations = Column(JSON, nullable=True)    # ["Meghalaya", "Kerala", "Goa"]
    liked_activities = Column(JSON, nullable=True)        # ["Trekking", "Waterfalls", "Photography"]
    
    average_trip_budget = Column(Float, default=800.0)
    average_trip_duration = Column(Integer, default=5)
    preferred_months = Column(JSON, nullable=True)        # ["October", "November"]
    visited_countries = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class TripPreferenceHistory(Base):
    __tablename__ = "trip_preference_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True)

    destination = Column(String(255), nullable=False)
    liked_categories = Column(JSON, nullable=True)        # ["waterfalls", "trekking", "food"]
    activities_completed = Column(JSON, nullable=True)    # list of completed activity titles
    rating = Column(Float, default=5.0)
    expense = Column(Float, default=500.0)
    duration = Column(Integer, default=5)
    month = Column(String(20), default="October")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")
    trip = relationship("Trip")


class DestinationKnowledge(Base):
    __tablename__ = "destination_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(255), nullable=False, unique=True, index=True)
    country = Column(String(255), nullable=False)
    
    categories = Column(JSON, nullable=True)              # ["nature", "waterfalls", "photography"]
    activities = Column(JSON, nullable=True)              # ["Living Root Bridges", "Dawki River Photography"]
    best_months = Column(JSON, nullable=True)              # ["October", "November", "December"]
    
    average_budget = Column(Float, default=500.0)
    weather_pattern = Column(String(255), default="Cool & Misty")
    travel_style = Column(String(100), default="Nature & Adventure")
    popularity_score = Column(Integer, default=85)        # 0-100 scale


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    destination = Column(String(255), nullable=False)
    match_score = Column(Integer, default=85)
    
    clicked = Column(Boolean, default=False)
    saved = Column(Boolean, default=False)
    booked = Column(Boolean, default=False)
    rating = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")
