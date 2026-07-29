from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), unique=True, nullable=False)
    
    total_budget = Column(Numeric(12, 2), nullable=False, default=0.00)
    currency = Column(String, nullable=False, default="USD")
    base_currency = Column(String, nullable=False, default="USD")
    exchange_rate_date = Column(Date, nullable=True)

    spent = Column(Numeric(12, 2), nullable=False, default=0.00)
    remaining = Column(Numeric(12, 2), nullable=False, default=0.00)
    daily_limit = Column(Numeric(12, 2), nullable=False, default=0.00)
    emergency_reserve = Column(Numeric(12, 2), nullable=False, default=0.00)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    trip = relationship("Trip", back_populates="budget_obj")
