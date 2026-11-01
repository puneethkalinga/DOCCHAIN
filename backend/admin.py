from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io, csv

from .database import get_db
from .models import User, AccessLog
from .utils import require_role

router = APIRouter(tags=["admin"])

# =============================
# Schemas
# =============================

class RoleUpdate(BaseModel):
    role: str

class UploadUpdate(BaseModel):
    enabled: bool


# =============================
# List users
# =============================

@router.get("/users")
def list_users(
    page: int = 1,
    page_size: int = 20,
    q: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    query = db.query(User)
    if q:
        query = query.filter(User.email.ilike(f"%{q}%"))

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "upload_enabled": u.upload_enabled,
                "mfa_enabled": u.mfa_enabled,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


# =============================
# Change role
# =============================

@router.patch("/users/{user_id}/role")
def update_role(
    user_id: str,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if payload.role not in ["admin", "staff", "recipient"]:
        raise HTTPException(400, "Invalid role")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return {"message": "Role updated", "id": user.id, "role": user.role}


# =============================
# Toggle uploads
# =============================

@router.patch("/users/{user_id}/upload")
def update_upload(
    user_id: str,
    payload: UploadUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.upload_enabled = payload.enabled
    db.commit()
    db.refresh(user)
    return {
        "message": "Upload permission updated",
        "id": user.id,
        "enabled": user.upload_enabled,
    }


# =============================
# Revoke user (soft disable)
# =============================

@router.patch("/users/{user_id}/revoke")
def revoke_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)
    return {"message": "User revoked", "id": user.id, "is_active": user.is_active}


# =============================
# Unrevoke user (reactivate)
# =============================

@router.patch("/users/{user_id}/unrevoke")
def unrevoke_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_active:
        raise HTTPException(400, "User is already active")

    user.is_active = True
    db.commit()
    db.refresh(user)
    return {"message": f"User {user.email} has been reactivated", "id": user.id, "is_active": user.is_active}


# =============================
# Logs (paginated)
# =============================

@router.get("/logs")
def list_logs(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    query = db.query(AccessLog)
    total = query.count()
    logs = (
        query.order_by(AccessLog.ts.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": l.id,
                "timestamp": l.ts.isoformat(),
                "user_email": l.actor.email if l.actor else None,
                "action": l.action,
                "details": f"Letter {l.letter_id}" if l.letter_id else "",
                "ip": l.ip,
            }
            for l in logs
        ],
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


# =============================
# Export logs as CSV
# =============================

@router.get("/logs/export")
def export_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    logs = db.query(AccessLog).order_by(AccessLog.ts.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["id", "timestamp", "user_email", "action", "details", "ip"])
    for l in logs:
        writer.writerow([
            l.id,
            l.ts.isoformat(),
            l.actor.email if l.actor else None,
            l.action,
            l.letter_id or "",
            l.ip or "",
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=access_logs.csv"},
    )
