import os, secrets
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .models import AccessLog, User
from .database import SessionLocal
from io import BytesIO
import qrcode

# -----------------------------
# JWT Config (production-friendly)
# -----------------------------
JWT_ISSUER = os.getenv("JWT_ISSUER", "docchain.local")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "docchain-api")
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")

# ⚠️ Production best practice: access = 15 min, refresh = 7 days
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "15"))
JWT_LEEWAY_SEC = int(os.getenv("JWT_LEEWAY_SEC", "30"))  # clock skew allowance (30s)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()

# -----------------------------
# Password Hashing
# -----------------------------
def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return pwd_ctx.verify(pw, pw_hash)

# -----------------------------
# JWT Tokens
# -----------------------------
def make_jwt(user: User, expires_minutes: int = JWT_EXPIRES_MIN) -> str:
    """
    Create a JWT for the given user.
    Default: short-lived (15m). Pass custom expires_minutes for refresh tokens.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode JWT.
    Enforces exp, iss, aud.
    Returns decoded payload if valid.
    """
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat"]},
            leeway=JWT_LEEWAY_SEC,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

# -----------------------------
# Auth Dependencies
# -----------------------------
def require_auth(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """
    Require a valid JWT AND check that user is still active.
    """
    payload = verify_jwt_token(creds.credentials)

    db: Session = SessionLocal()
    user = db.query(User).get(payload.get("sub"))
    db.close()

    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Account revoked or inactive")

    return payload

def optional_auth(creds: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """
    Allow anonymous access, but validate JWT if provided.
    """
    if not creds:
        return None
    payload = verify_jwt_token(creds.credentials)

    db: Session = SessionLocal()
    user = db.query(User).get(payload.get("sub"))
    db.close()

    if not user or not user.is_active:
        return None  # treat revoked user as anonymous

    return payload

def require_role(required):
    """
    Enforce a single required role.
    """
    def _checker(payload=Depends(require_auth)):
        if payload.get("role") != required:
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    return _checker

def require_any(*roles):
    """
    Enforce one-of-many roles.
    """
    def _checker(payload=Depends(require_auth)):
        if payload.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    return _checker

# -----------------------------
# OTP
# -----------------------------
def gen_otp() -> str:
    """Generate a 6-digit OTP code."""
    return str(secrets.randbelow(900000) + 100000)

# -----------------------------
# Logging
# -----------------------------
def log_action(db: Session, letter_id, actor_user_id, action: str, req: Request):
    log = AccessLog(
        letter_id=letter_id,
        actor_user_id=actor_user_id,
        action=action,
        ip=(req.client.host if req and req.client else None),
        user_agent=(req.headers.get("user-agent") if req else None),
    )
    db.add(log)
    db.commit()

# -----------------------------
# Hash Display Helper
# -----------------------------
def hash_prefix(full_hash: str, length: int = 8) -> str:
    """Return a shortened prefix of a hash string for display purposes."""
    if not full_hash:
        return ""
    return full_hash[:length]

# -----------------------------
# QR Code Generator
# -----------------------------
def generate_qr_code(data: str) -> BytesIO:
    """Generate a PNG QR code from the given data and return a BytesIO buffer."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
