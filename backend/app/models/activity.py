from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String(50), default="activity") # Identifier for frontend icon
    color = Column(String(50), default="blue") # Identifier for frontend color
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")
