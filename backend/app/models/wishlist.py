from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wishlist_items")
