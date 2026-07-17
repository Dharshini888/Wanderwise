from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.connection import Base

class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=True) # e.g., Navigator, Budget Keeper, Photographer
    is_admin = Column(Boolean, default=False)

    trip = relationship("Trip")
    user = relationship("User")

class ConsensusVote(Base):
    __tablename__ = "consensus_votes"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(String, nullable=False) # ID of place/activity from third-party or DB
    vote = Column(Boolean, nullable=False) # True = Yes, False = No

    trip = relationship("Trip")
    user = relationship("User")
