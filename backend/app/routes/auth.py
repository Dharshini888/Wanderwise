from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.database.connection import get_db
from app.models.user import User
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone_number: Optional[str] = None
    preferred_budget: Optional[str] = None
    currency: Optional[str] = "USD"
    travel_styles: Optional[str] = None
    preferred_climate: Optional[str] = None
    preferred_activities: Optional[str] = None
    languages: Optional[str] = None
    dietary_preferences: Optional[str] = None
    accessibility_needs: Optional[str] = None
    avatar_url: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_budget: Optional[str] = None
    currency: Optional[str] = None
    travel_styles: Optional[str] = None
    preferred_climate: Optional[str] = None
    preferred_activities: Optional[str] = None
    languages: Optional[str] = None
    dietary_preferences: Optional[str] = None
    accessibility_needs: Optional[str] = None


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": getattr(user, "role", "USER"),
        "profile_completed": getattr(user, "profile_completed", False),
        "avatar_url": getattr(user, "avatar_url", None) or getattr(user, "profile_picture", None),
        "is_active": getattr(user, "is_active", True),
        "last_login_at": user.last_login_at.isoformat() if getattr(user, "last_login_at", None) else None,
        "phone_number": user.phone_number,
        "preferred_budget": user.preferred_budget,
        "currency": user.currency or "USD",
        "travel_styles": user.travel_styles,
        "preferred_climate": user.preferred_climate,
        "preferred_activities": user.preferred_activities,
        "languages": user.languages,
        "dietary_preferences": user.dietary_preferences,
        "accessibility_needs": user.accessibility_needs,
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
    }


oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    token_type = payload.get("type")
    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or missing",
        )
    return user


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if not user_id or token_type != "access":
            return None
        return db.query(User).filter(User.id == int(user_id)).first()
    except Exception:
        return None



@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user in WanderWise.
    
    Request:
      - name: String (2-100 chars)
      - email: Valid email address
      - password: String (min 6 chars)
      
    Response (201 Created):
      - access_token: Short-lived JWT access token
      - refresh_token: Long-lived JWT refresh token
      - user: Complete User Profile Object
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    is_completed = bool(data.preferred_budget or data.travel_styles or data.preferred_activities)

    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role="USER",
        profile_completed=is_completed,
        avatar_url=data.avatar_url,
        phone_number=data.phone_number,
        preferred_budget=data.preferred_budget,
        currency=data.currency or "USD",
        travel_styles=data.travel_styles,
        preferred_climate=data.preferred_climate,
        preferred_activities=data.preferred_activities,
        languages=data.languages,
        dietary_preferences=data.dietary_preferences,
        accessibility_needs=data.accessibility_needs,
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user credentials and issue JWT tokens.
    
    Request:
      - email: Registered email
      - password: User password
      - remember_me: Boolean (If True, extends session expiry)
      
    Response (200 OK):
      - access_token: JWT access token
      - refresh_token: JWT refresh token
      - user: Authenticated User Object
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token_data = {"sub": str(user.id), "email": user.email, "role": getattr(user, "role", "USER")}

    if data.remember_me:
        access_token = create_access_token(token_data, expires_delta=timedelta(days=30))
        refresh_token = create_refresh_token(token_data, expires_delta=timedelta(days=30))
    else:
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


@router.post("/refresh")
def refresh_token_endpoint(data: RefreshRequest, db: Session = Depends(get_db)):
    """
    Obtain a new access_token using a valid refresh_token.
    """
    payload = decode_token(data.refresh_token)
    user_id = payload.get("sub")
    token_type = payload.get("type")

    if not user_id or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {"sub": str(user.id), "email": user.email, "role": getattr(user, "role", "USER")}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


@router.post("/logout")
def logout():
    """
    Logout current user session.
    """
    return {"message": "Logged out successfully"}


@router.get("/verify")
def verify_session(current_user: User = Depends(get_current_user)):
    """
    Verify if the current Bearer token is valid and active.
    """
    return {"valid": True, "user": user_to_dict(current_user)}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Fetch authenticated user details.
    """
    return user_to_dict(current_user)


@router.put("/me")
@router.put("/me/preferences")
def update_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update profile details & travel preferences for current user.
    Automatically marks profile_completed = True if required preferences are configured.
    """
    for field, val in data.dict(exclude_unset=True).items():
        if hasattr(current_user, field) and val is not None:
            setattr(current_user, field, val)

    if current_user.preferred_budget or current_user.travel_styles or current_user.preferred_activities:
        current_user.profile_completed = True

    db.commit()
    db.refresh(current_user)
    return user_to_dict(current_user)
