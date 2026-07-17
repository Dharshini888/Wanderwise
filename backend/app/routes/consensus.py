from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database.connection import get_db
from app.models.group import ConsensusVote, GroupMember
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/consensus", tags=["Consensus"])

class VoteRequest(BaseModel):
    trip_id: int
    activity_id: str
    vote: bool

class ConflictResolutionResponse(BaseModel):
    activity_id: str
    yes_votes: int
    no_votes: int
    ai_suggestion: str

@router.post("/vote")
def record_vote(
    vote_data: VoteRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verify user is part of the group trip
    member = db.query(GroupMember).filter(
        GroupMember.trip_id == vote_data.trip_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this trip")

    # Record or update vote
    existing_vote = db.query(ConsensusVote).filter(
        ConsensusVote.trip_id == vote_data.trip_id,
        ConsensusVote.user_id == current_user.id,
        ConsensusVote.activity_id == vote_data.activity_id
    ).first()

    if existing_vote:
        existing_vote.vote = vote_data.vote
    else:
        new_vote = ConsensusVote(
            trip_id=vote_data.trip_id,
            user_id=current_user.id,
            activity_id=vote_data.activity_id,
            vote=vote_data.vote
        )
        db.add(new_vote)

    db.commit()
    return {"message": "Vote recorded successfully"}

@router.get("/{trip_id}/resolution", response_model=List[ConflictResolutionResponse])
def get_conflict_resolution(
    trip_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Simplified logic: aggregate votes
    votes = db.query(ConsensusVote).filter(ConsensusVote.trip_id == trip_id).all()
    
    activity_tallies = {}
    for v in votes:
        if v.activity_id not in activity_tallies:
            activity_tallies[v.activity_id] = {"yes": 0, "no": 0}
        if v.vote:
            activity_tallies[v.activity_id]["yes"] += 1
        else:
            activity_tallies[v.activity_id]["no"] += 1
            
    resolutions = []
    for activity_id, tally in activity_tallies.items():
        total = tally["yes"] + tally["no"]
        if total == 0:
            continue
        
        yes_pct = tally["yes"] / total
        
        # Placeholder AI Suggestion Logic
        suggestion = "Approved by majority."
        if yes_pct < 0.5:
            suggestion = "Consider alternative activity due to low group interest."
        elif 0.5 <= yes_pct < 0.8:
            suggestion = "Split group or find a compromise time slot."

        resolutions.append(ConflictResolutionResponse(
            activity_id=activity_id,
            yes_votes=tally["yes"],
            no_votes=tally["no"],
            ai_suggestion=suggestion
        ))
        
    return resolutions
