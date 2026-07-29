# TODO Phase 2: Full booking import service, QR code processing, and flight status tracking.
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class TripBooking(Base):
    __tablename__ = "trip_bookings"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    
    type = Column(String, nullable=False)  # flight, hotel, train, bus, taxi, activity, restaurant, car_rental
    booking_id = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    confirmation_number = Column(String, nullable=True)
    status = Column(String, default="confirmed")  # pending, confirmed, cancelled
    
    amount = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    booking_url = Column(String, nullable=True)
    booking_date = Column(DateTime(timezone=True), nullable=True)
    payment_status = Column(String, default="paid")  # paid, pending, unpaid
    
    qr_code_data = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)  # JSON string of attachment URLs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    trip = relationship("Trip", back_populates="bookings")
