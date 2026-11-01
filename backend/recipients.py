# =============================================
# recipients.py — Final Version
# =============================================

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .database import get_db
from .models import Letter, User
from .utils import require_auth, log_action, hash_prefix

router = APIRouter(prefix="/recipients", tags=["recipients"])

# ------------------------------------------------------------------
# List all letters for the logged-in recipient
# ------------------------------------------------------------------
@router.get("/me/letters")
def list_my_letters(
    request: Request,
    q: str = Query(None, description="Search by filename or sender email"),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    payload = Depends(require_auth),
):
    """Return all letters belonging to the current recipient."""

    if payload.get("role") != "recipient":
        raise HTTPException(status_code=403, detail="Only recipients can view their letters.")

    user_id = payload["sub"]

    query = (
        db.query(Letter)
        .filter(Letter.recipient_user_id == user_id)
        .join(User, Letter.sender_user_id == User.id, isouter=True)
    )

    if q:
        q_lower = q.lower()
        query = query.filter(
            or_(
                Letter.file_name_original.ilike(f"%{q_lower}%"),
                User.email.ilike(f"%{q_lower}%"),
            )
        )
    if status:
        query = query.filter(Letter.status == status)

    letters = query.order_by(Letter.created_at.desc()).all()

    rows = []
    for l in letters:
        rows.append({
            "id": l.id,
            "file_name": l.file_name_original or "Untitled.pdf",
            "hash_prefix": hash_prefix(l.sha256) if l.sha256 else None,
            "sender_email": (l.sender.email if l.sender else None),
            "uploaded_at": l.created_at.isoformat(),
            "expires_at": l.expires_at.isoformat() if l.expires_at else None,
            "status": l.status,
            "download_url": f"/api/letters/{l.id}/download",
            "inline_url": f"/api/letters/{l.id}/inline",
            "preview_url": f"/api/letters/{l.id}/preview",
        })

    log_action(db, None, user_id, "recipient_list_letters", request)
    return {"total": len(rows), "items": rows}


# ------------------------------------------------------------------
# Optional health check
# ------------------------------------------------------------------
@router.get("/ping")
def ping_recipient():
    return {"ok": True, "msg": "Recipient router active"}
