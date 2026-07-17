from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    trip = relationship("Trip", back_populates="expenses")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete")

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_owed = Column(Float, nullable=False)
    is_settled = Column(Boolean, default=False)

    expense = relationship("Expense", back_populates="splits")
