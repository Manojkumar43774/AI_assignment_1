import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import (
    create_access_token,
    create_oauth_state,
    generate_otp,
    get_current_user,
    hash_secret,
    verify_oauth_state,
    verify_secret,
)
from ..config import settings
from ..database import get_db
from ..email_utils import send_otp_email
from ..models import PendingPasswordReset, PendingSignup, User
from ..schemas import (
    LoginRequest,
    MessageOut,
    PasswordResetRequestOtp,
    PasswordResetVerify,
    SignupRequestOtp,
    SignupVerifyOtp,
    TokenOut,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _require_google_creds() -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env",
        )


def _unique_username(db: Session, base: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "", base)[:40] or "user"
    candidate = cleaned
    n = 1
    while db.query(User).filter(User.username == candidate).first():
        candidate = f"{cleaned}{n}"
        n += 1
    return candidate


def _upsert_oauth_user(
    db: Session,
    *,
    provider: str,
    oauth_id: str,
    email: str,
    preferred_username: str,
) -> User:
    user = (
        db.query(User)
        .filter(User.oauth_provider == provider, User.oauth_id == oauth_id)
        .first()
    )
    if user:
        return user

    by_email = db.query(User).filter(User.email == email).first()
    if by_email:
        by_email.oauth_provider = provider
        by_email.oauth_id = oauth_id
        db.commit()
        db.refresh(by_email)
        return by_email

    user = User(
        username=_unique_username(db, preferred_username),
        email=email,
        oauth_provider=provider,
        oauth_id=oauth_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _frontend_token_redirect(token: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={token}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/providers")
def list_providers():
    return {
        "google": bool(settings.google_client_id and settings.google_client_secret),
    }


@router.get("/google")
def google_login():
    _require_google_creds()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": create_oauth_state("google"),
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    verify_oauth_state(state, "google")
    _require_google_creds()

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google code")
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No Google access token returned")

        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google profile")
        info = userinfo_res.json()

    email = info.get("email")
    oauth_id = info.get("sub")
    if not email or not oauth_id:
        raise HTTPException(status_code=400, detail="Google account missing email")

    preferred = info.get("name") or email.split("@")[0]
    user = _upsert_oauth_user(
        db,
        provider="google",
        oauth_id=oauth_id,
        email=email,
        preferred_username=preferred,
    )
    app_token = create_access_token({"sub": user.username})
    return _frontend_token_redirect(app_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/signup/request-otp", response_model=MessageOut)
def signup_request_otp(body: SignupRequestOtp, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(
            status_code=400,
            detail="That username is already taken. Please choose a different one.",
        )

    otp = generate_otp()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.otp_expire_minutes)

    pending = db.query(PendingSignup).filter(PendingSignup.email == body.email).first()
    if pending is None:
        pending = PendingSignup(email=body.email)
        db.add(pending)

    pending.username = body.username
    pending.first_name = body.first_name
    pending.last_name = body.last_name
    pending.password_hash = hash_secret(body.password)
    pending.otp_hash = hash_secret(otp)
    pending.otp_expires_at = expires_at
    pending.attempt_count = 0

    send_otp_email(body.email, otp)

    db.commit()
    return {"message": "Verification code sent"}


@router.post("/signup/verify-otp", response_model=TokenOut)
def signup_verify_otp(body: SignupVerifyOtp, db: Session = Depends(get_db)):
    pending = db.query(PendingSignup).filter(PendingSignup.email == body.email).first()
    if pending is None:
        raise HTTPException(status_code=400, detail="No pending signup found for this email")

    now = datetime.now(timezone.utc)
    expires_at = pending.otp_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code expired, please sign up again")

    if pending.attempt_count >= settings.otp_max_attempts:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="Too many incorrect attempts, please sign up again")

    if not verify_secret(body.otp, pending.otp_hash):
        pending.attempt_count += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect verification code")

    if db.query(User).filter(User.email == pending.email).first():
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    if db.query(User).filter(User.username == pending.username).first():
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="That username was just taken by someone else. Please sign up again with a different one.",
        )

    user = User(
        username=pending.username,
        email=pending.email,
        oauth_provider="email",
        oauth_id=pending.email,
        first_name=pending.first_name,
        last_name=pending.last_name,
        password_hash=pending.password_hash,
    )
    db.add(user)
    db.delete(pending)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username})
    return {"access_token": token}


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not user.password_hash:
        if user is not None and not user.password_hash:
            raise HTTPException(
                status_code=400,
                detail="This account uses Google sign-in. Continue with Google instead.",
            )
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not verify_secret(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token}


_RESET_REQUESTED_MESSAGE = "If that email is registered, we've sent a reset code"


@router.post("/password/request-otp", response_model=MessageOut)
def password_request_otp(body: PasswordResetRequestOtp, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not user.password_hash:
        return {"message": _RESET_REQUESTED_MESSAGE}

    otp = generate_otp()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.otp_expire_minutes)

    pending = (
        db.query(PendingPasswordReset)
        .filter(PendingPasswordReset.email == body.email)
        .first()
    )
    if pending is None:
        pending = PendingPasswordReset(email=body.email)
        db.add(pending)

    pending.otp_hash = hash_secret(otp)
    pending.otp_expires_at = expires_at
    pending.attempt_count = 0

    send_otp_email(body.email, otp)

    db.commit()
    return {"message": _RESET_REQUESTED_MESSAGE}


@router.post("/password/reset", response_model=TokenOut)
def password_reset(body: PasswordResetVerify, db: Session = Depends(get_db)):
    pending = (
        db.query(PendingPasswordReset)
        .filter(PendingPasswordReset.email == body.email)
        .first()
    )
    if pending is None:
        raise HTTPException(status_code=400, detail="No password reset requested for this email")

    now = datetime.now(timezone.utc)
    expires_at = pending.otp_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code expired, please request a new one")

    if pending.attempt_count >= settings.otp_max_attempts:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="Too many incorrect attempts, please request a new code")

    if not verify_secret(body.otp, pending.otp_hash):
        pending.attempt_count += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect verification code")

    user = db.query(User).filter(User.email == pending.email).first()
    if user is None:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="No password reset requested for this email")

    user.password_hash = hash_secret(body.new_password)
    db.delete(pending)
    db.commit()

    token = create_access_token({"sub": user.username})
    return {"access_token": token}
