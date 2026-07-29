from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, default="sightseeing")  # sightseeing, restaurant, hotel, shopping, transit, etc.
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True)
    rating = Column(Float, default=4.5)
    opening_hours = Column(String, nullable=True)
    ticket_price = Column(Float, default=0.0)
    google_maps_url = Column(String, nullable=True)
    osm_id = Column(String, nullable=True)
    place_id = Column(String, nullable=True, index=True)
    google_place_id = Column(String, nullable=True, index=True)
    timezone = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    categories = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
  # Comma-separated or JSON string tags

    activities = relationship("ItineraryActivity", back_populates="place")
