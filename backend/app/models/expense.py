from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, DateTime, JSON, Boolean, Enum as SQLEnum

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
from app.models.enums import ExpenseCategory, PaymentMethod, ExpenseSource

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    title = Column(String, nullable=False, default="Expense")
    merchant_normalized = Column(String, nullable=True, index=True)
    description = Column(String, nullable=True)
    
    # Financial precision with Numeric(12, 2)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    base_currency = Column(String, nullable=False, default="USD")
    exchange_rate = Column(Numeric(12, 6), default=1.0)

    category = Column(SQLEnum(ExpenseCategory), nullable=False, default=ExpenseCategory.MISC)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False, default=PaymentMethod.CASH)
    expense_date = Column(Date, nullable=False)
    location_name = Column(String, nullable=True)
    
    receipt_metadata = Column(JSON, nullable=True)  # {filename, url, ocr_status, ocr_confidence}
    notes = Column(String, nullable=True)
    expense_source = Column(SQLEnum(ExpenseSource), nullable=False, default=ExpenseSource.MANUAL)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trip = relationship("Trip", back_populates="expenses")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete")

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_owed = Column(Numeric(12, 2), nullable=False)
    is_settled = Column(Boolean, default=False)

    expense = relationship("Expense", back_populates="splits")
