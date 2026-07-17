from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
    document_type = Column(String, nullable=False) # e.g., Passport, Visa, Insurance
    encrypted_url = Column(String, nullable=False) # URL to encrypted storage
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User")
    trip = relationship("Trip")
