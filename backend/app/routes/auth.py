import os
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
import httpx

from app.database.connection import get_db
from app.models.user import User
from app.core.budget_tiers import normalize_budget_tier
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class GoogleAuthRequest(BaseModel):
    code: Optional[str] = None
    id_token: Optional[str] = None
    redirect_uri: Optional[str] = None


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
        "auth_provider": getattr(user, "auth_provider", "local") or "local",
        "google_id": getattr(user, "google_id", None),
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

    canonical_budget = normalize_budget_tier(data.preferred_budget) if data.preferred_budget else None
    is_completed = bool(canonical_budget or data.travel_styles or data.preferred_activities)

    user = User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        auth_provider="local",
        role="USER",
        profile_completed=is_completed,
        avatar_url=data.avatar_url,
        phone_number=data.phone_number,
        preferred_budget=canonical_budget,
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
            if field == "preferred_budget":
                val = normalize_budget_tier(val)
            setattr(current_user, field, val)

    if current_user.preferred_budget or current_user.travel_styles or current_user.preferred_activities:
        current_user.profile_completed = True

    db.commit()
    db.refresh(current_user)
    return user_to_dict(current_user)


@router.get("/google/url")
def get_google_auth_url(redirect_uri: Optional[str] = None):
    """
    Returns the Google OAuth authorization URL.
    Checks whether GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are configured.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return {
            "configured": False,
            "error": "Google OAuth is not configured on this server.",
            "required_vars": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
            "setup_help": "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env to enable Google Sign-In."
        }

    cb = redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    params = {
        "client_id": client_id,
        "redirect_uri": cb,
        "response_type": "code",
        "scope": "openid profile email",
        "access_type": "offline",
        "prompt": "select_account",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {
        "configured": True,
        "auth_url": auth_url,
    }


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle the OAuth redirect callback from Google.
    Exchanges authorization code for tokens, retrieves profile, creates or signs in user,
    and redirects the browser to the frontend callback handler.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    if error:
        err_param = urllib.parse.quote(error)
        return RedirectResponse(url=f"{frontend_url}/auth/callback?error={err_param}")

    if not code:
        return RedirectResponse(url=f"{frontend_url}/auth/callback?error=missing_code")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

    if not client_id or not client_secret:
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?error=unconfigured_oauth&details=Missing+GOOGLE_CLIENT_ID+or+GOOGLE_CLIENT_SECRET"
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                err_text = token_resp.text
                return RedirectResponse(
                    url=f"{frontend_url}/auth/callback?error=token_exchange_failed&details={urllib.parse.quote(err_text[:120])}"
                )

            token_json = token_resp.json()
            google_access_token = token_json.get("access_token")

            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"},
            )
            if userinfo_resp.status_code != 200:
                return RedirectResponse(url=f"{frontend_url}/auth/callback?error=failed_fetching_userinfo")

            user_info = userinfo_resp.json()
    except Exception as exc:
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?error=network_error&details={urllib.parse.quote(str(exc)[:120])}"
        )

    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name") or (email.split("@")[0] if email else "Wanderer")
    picture = user_info.get("picture")

    if not email:
        return RedirectResponse(url=f"{frontend_url}/auth/callback?error=no_email_returned")

    # Look up existing user by google_id or email
    user = None
    if google_id:
        user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    is_new = False
    if not user:
        is_new = True
        user = User(
            name=name,
            email=email,
            google_id=google_id,
            auth_provider="google",
            avatar_url=picture,
            role="USER",
            profile_completed=False,
            currency="USD",
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.google_id and google_id:
            user.google_id = google_id
        if not user.avatar_url and picture:
            user.avatar_url = picture
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

    token_data = {"sub": str(user.id), "email": user.email, "role": getattr(user, "role", "USER")}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    dest_path = "/profile" if (is_new or not user.profile_completed) else "/dashboard"
    callback_url = (
        f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        f"&is_new={'true' if is_new else 'false'}&redirect_to={dest_path}"
    )
    return RedirectResponse(url=callback_url)


@router.post("/google")
async def google_auth_api(data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Programmatic endpoint for Google Sign-In (for SPA or mobile flow).
    Accepts either an authorization 'code' (exchanged for tokens) or an 'id_token'.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured on this server. Missing GOOGLE_CLIENT_ID.",
        )

    user_info = None

    if data.code:
        if not client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google OAuth configuration incomplete. Missing GOOGLE_CLIENT_SECRET.",
            )
        redirect_uri = data.redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "postmessage")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": data.code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                if token_resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to exchange Google authorization code: {token_resp.text}",
                    )
                token_json = token_resp.json()
                google_access_token = token_json.get("access_token")
                userinfo_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {google_access_token}"},
                )
                if userinfo_resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to fetch user profile from Google",
                    )
                user_info = userinfo_resp.json()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google authentication network error: {str(exc)}",
            )
    elif data.id_token:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={data.id_token}"
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid Google ID token",
                    )
                token_info = resp.json()
                if token_info.get("aud") != client_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Google ID token audience mismatch",
                    )
                user_info = token_info
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating Google token: {str(exc)}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either code or id_token must be provided",
        )

    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name") or (email.split("@")[0] if email else "Wanderer")
    picture = user_info.get("picture")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not provide a valid email address.",
        )

    user = None
    if google_id:
        user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    is_new = False
    if not user:
        is_new = True
        user = User(
            name=name,
            email=email,
            google_id=google_id,
            auth_provider="google",
            avatar_url=picture,
            role="USER",
            profile_completed=False,
            currency="USD",
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.google_id and google_id:
            user.google_id = google_id
        if not user.avatar_url and picture:
            user.avatar_url = picture
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

    token_data = {"sub": str(user.id), "email": user.email, "role": getattr(user, "role", "USER")}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_to_dict(user),
        "is_new": is_new,
        "redirect_to": "/profile" if (is_new or not user.profile_completed) else "/dashboard",
    }
