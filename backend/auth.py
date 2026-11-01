from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import hmac, os, secrets

from .database import get_db
from .models import User, RefreshToken
from .schemas import SignupIn, LoginIn, VerifyOtpIn
from .utils import (
    hash_password, verify_password, make_jwt, gen_otp
)

ACCESS_EXP_MIN = int(os.getenv("ACCESS_EXP_MIN", "15"))   # Access token = 15m
REFRESH_EXP_DAYS = int(os.getenv("REFRESH_EXP_DAYS", "7")) # Refresh token = 7d
OTP_EXP_MIN = int(os.getenv("OTP_EXP_MIN", "5"))

router = APIRouter()


# =========================
# Helpers
# =========================
def issue_tokens(db: Session, user: User):
    """Generate new access + refresh tokens and persist refresh."""
    access_token = make_jwt(user, expires_minutes=ACCESS_EXP_MIN)

    refresh_token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXP_DAYS)

    db.add(RefreshToken(user_id=user.id, token=refresh_token, expires_at=expires_at))
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "upload_enabled": user.upload_enabled,
        }
    }


# =========================
# Sign up
# =========================
@router.post("/signup")
def signup(data: SignupIn, db: Session = Depends(get_db)):
    email_l = data.email.lower()
    existing = db.query(User).filter(User.email == email_l).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email_l,
        password_hash=hash_password(data.password),
        role=data.role,
        mfa_enabled=data.mfa_enabled,
        phone_number=data.phone_number,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "mfa_enabled": user.mfa_enabled,
        "phone_number": user.phone_number,
        "is_active": user.is_active,
        "upload_enabled": user.upload_enabled,
    }


# =========================
# Login
# =========================
@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account revoked. Contact admin.")

    # Admin: bypass OTP for convenience
    if user.role == "admin":
        return issue_tokens(db, user)

    # MFA flow
    if user.mfa_enabled:
        otp = gen_otp()
        user.last_otp = otp
        user.last_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXP_MIN)
        db.commit()
        print(f"[DEV] OTP for {user.email}: {otp} (expires in {OTP_EXP_MIN} min)")
        return {"mfa_required": True, "message": "OTP sent"}
    else:
        return issue_tokens(db, user)


# =========================
# Verify OTP
# =========================
@router.post("/verify-otp")
def verify_otp(data: VerifyOtpIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA not enabled")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account revoked. Contact admin.")

    if (
        not user.last_otp
        or not user.last_otp_expires_at
        or datetime.now(timezone.utc) > user.last_otp_expires_at
    ):
        raise HTTPException(status_code=401, detail="OTP expired or not issued")

    if not hmac.compare_digest(user.last_otp, data.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # reset OTP after successful use
    user.last_otp = None
    user.last_otp_expires_at = None
    db.commit()

    return issue_tokens(db, user)


# =========================
# Refresh token
# =========================
@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User revoked or not found")

    # 🔹 Rotate refresh token: delete old one
    db.delete(token)
    db.commit()

    return issue_tokens(db, user)
