import os, uuid, base64, hashlib, tempfile, json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from io import BytesIO

from .database import get_db
from .models import Letter, VerificationToken, User
from .utils import require_any, optional_auth, log_action, hash_prefix, generate_qr_code
from .crypto import aes_encrypt, aes_decrypt
from .notifications import (
    notify_recipient_new_letter,
    notify_recipient_revoked,
)

# PDF handling
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Azure Blob
from azure.storage.blob import BlobServiceClient
AZURE_STORAGE_CONN_STR = os.getenv("AZURE_STORAGE_CONN_STR")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "letters")
blob_svc = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONN_STR)
blob_container = blob_svc.get_container_client(AZURE_STORAGE_CONTAINER)

router = APIRouter()

# -----------------------------
# Helper: Add Verified Seal + QR to first page
# -----------------------------
def embed_verified_and_qr(pdf_bytes: bytes, qr_data: str) -> bytes:
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Correct path to backend/assets/verified.png
    verified_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "assests", "verified.png")
    )
    if not os.path.exists(verified_path):
        raise RuntimeError(f"Verified icon not found at {verified_path}")

    verified_img = ImageReader(verified_path)

    # Generate QR buffer
    qr_buf = generate_qr_code(qr_data)
    qr_img = ImageReader(qr_buf)

    # Get dimensions of first page
    first_page = reader.pages[0]
    w = float(first_page.mediabox.width)
    h = float(first_page.mediabox.height)

    # Create overlay
    overlay_buf = BytesIO()
    c = canvas.Canvas(overlay_buf, pagesize=(w, h))

    # Draw QR (50x50) slightly left
    c.drawImage(qr_img, w - 110, h - 60, width=50, height=50, mask="auto")

    # Draw verified seal (30x30) to the right
    c.drawImage(verified_img, w - 55, h - 55, width=30, height=30, mask="auto")

    c.save()
    overlay_buf.seek(0)

    # Merge overlay with first page
    overlay_pdf = PdfReader(overlay_buf)
    first_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(first_page)

    # Add remaining pages unchanged
    for p in reader.pages[1:]:
        writer.add_page(p)

    out_buf = BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()

# -----------------------------
# Upload (Single OR Multi-recipient)
# -----------------------------
@router.post("")
async def upload_letter(
    request: Request,
    recipient_email: str = Form(None),
    recipient_emails: str = Form(None),
    sensitivity: str = Form("low"),
    expires_at: str = Form(None),
    file: UploadFile = File(...),
    payload = Depends(require_any("staff", "admin")),
    db: Session = Depends(get_db),
):
    # Parse recipients
    recipients = []
    if recipient_emails:
        try:
            if recipient_emails.strip().startswith("["):
                recipients = json.loads(recipient_emails)
            else:
                recipients = [r.strip() for r in recipient_emails.split(",") if r.strip()]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid recipient_emails format")
    elif recipient_email:
        recipients = [recipient_email.strip()]

    if not recipients:
        raise HTTPException(status_code=400, detail="No recipients provided")

    # Validate recipients in DB
    db_recipients = []
    for email in recipients:
        recip = db.query(User).filter(User.email == email.lower()).first()
        if not recip:
            raise HTTPException(status_code=404, detail=f"Recipient not found: {email}")
        db_recipients.append(recip)

    # Expiry handling
    exp_dt = datetime.utcnow() + timedelta(days=30)
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at.replace("Z", ""))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid expires_at format")

    results = []
    raw_original = await file.read()

    for recip in db_recipients:
        token_bytes = os.urandom(32)
        token = base64.urlsafe_b64encode(token_bytes).decode().rstrip("=")
        verify_url = f"https://your-frontend-domain/verify.html?token={token}"

        if file.filename.lower().endswith(".pdf"):
            pdf_final = embed_verified_and_qr(raw_original, verify_url)
        else:
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        sha256 = hashlib.sha256(pdf_final).hexdigest()
        cipher, iv, tag = aes_encrypt(pdf_final)

        blob_id = str(uuid.uuid4())
        blob_name = f"letters/{blob_id}.bin"
        blob_container.upload_blob(name=blob_name, data=cipher, overwrite=True)

        letter_id = str(uuid.uuid4())
        letter = Letter(
            id=letter_id,
            sender_user_id=payload["sub"],
            recipient_user_id=recip.id,
            sha256=sha256,
            file_name_original=file.filename,
            blob_path=blob_name,
            iv_b64=base64.b64encode(iv).decode(),
            tag_b64=base64.b64encode(tag).decode(),
            sensitivity=sensitivity,
            status="active",
            created_at=datetime.utcnow(),
            expires_at=exp_dt
        )
        db.add(letter)
        db.commit()

        vt = VerificationToken(
            letter_id=letter_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=30),
            used=False
        )
        db.add(vt)
        db.commit()

        log_action(db, letter_id, payload["sub"], "upload", request)
        notify_recipient_new_letter(recip.email, letter_id, recip.phone_number)

        results.append({
            "id": letter_id,
            "recipient": recip.email,
            "token": token,
            "hash_prefix": hash_prefix(sha256),
            "verify_url": f"verify.html?token={token}",
            "sensitivity": sensitivity,
            "status": "active"
        })

    return {"letters": results}

# -----------------------------
# List with Search & Filters
# -----------------------------
@router.get("")
def list_letters(
    request: Request,
    q: str = Query(None),
    status: str = Query(None),
    uploaded_after: datetime = Query(None),
    uploaded_before: datetime = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    payload = Depends(optional_auth),
    db: Session = Depends(get_db),
):
    query = db.query(Letter)
    if payload:
        if payload["role"] == "recipient":
            query = query.filter(Letter.recipient_user_id == payload["sub"])
        elif payload["role"] == "staff":
            query = query.filter(Letter.sender_user_id == payload["sub"])
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if q:
        q_lower = q.lower()
        query = query.join(User, Letter.recipient_user_id == User.id, isouter=True)
        query = query.filter(
            or_(
                Letter.id.ilike(f"%{q_lower}%"),
                Letter.file_name_original.ilike(f"%{q_lower}%"),
                User.email.ilike(f"%{q_lower}%")
            )
        )

    if status:
        query = query.filter(Letter.status == status)

    if uploaded_after:
        query = query.filter(Letter.created_at >= uploaded_after)
    if uploaded_before:
        query = query.filter(Letter.created_at <= uploaded_before)

    total = query.count()
    items = (query.order_by(Letter.created_at.desc())
                  .offset((page-1)*page_size)
                  .limit(page_size)
                  .all())

    return {
        "total": total,
        "pages": (total + page_size - 1) // page_size or 1,
        "items": [{
            "id": l.id,
            "file_name": l.file_name_original,
            "status": l.status,
            "hash_prefix": hash_prefix(l.sha256),
            "created_at": l.created_at.isoformat(),
            "expires_at": l.expires_at.isoformat() if l.expires_at else None,
            "recipient_email": (l.recipient.email if l.recipient else None),
            "sender_email": (l.sender.email if l.sender else None)
        } for l in items]
    }

# -----------------------------
# Download (attachment)
# -----------------------------
@router.get("/{letter_id}/download")
def download_letter(
    letter_id: str,
    request: Request,
    token: str = None,
    payload = Depends(optional_auth),
    db: Session = Depends(get_db),
):
    letter = db.get(Letter, letter_id)
    if not letter or letter.status != "active":
        raise HTTPException(status_code=404, detail="Letter not found")

    blob = blob_container.download_blob(letter.blob_path)
    cipher = blob.readall()
    iv = base64.b64decode(letter.iv_b64)
    tag = base64.b64decode(letter.tag_b64)
    plain = aes_decrypt(cipher, iv, tag)

    log_action(db, letter_id, None, "download", request)
    filename = letter.file_name_original or f"{letter_id}.pdf"
    return StreamingResponse(
        BytesIO(plain),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# -----------------------------
# Inline (embed in iframe)
# -----------------------------
@router.get("/{letter_id}/inline")
def inline_letter(
    letter_id: str,
    request: Request,
    payload = Depends(optional_auth),
    db: Session = Depends(get_db),
):
    letter = db.get(Letter, letter_id)
    if not letter or letter.status != "active":
        raise HTTPException(status_code=404, detail="Letter not found")

    blob = blob_container.download_blob(letter.blob_path)
    cipher = blob.readall()
    iv = base64.b64decode(letter.iv_b64)
    tag = base64.b64decode(letter.tag_b64)
    plain = aes_decrypt(cipher, iv, tag)

    filename = letter.file_name_original or f"{letter_id}.pdf"
    log_action(db, letter_id, None, "inline", request)
    return StreamingResponse(
        BytesIO(plain),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )

# -----------------------------
# Preview (text extract)
# -----------------------------
@router.get("/{letter_id}/preview")
def preview_letter(
    letter_id: str,
    request: Request,
    payload = Depends(optional_auth),
    db: Session = Depends(get_db),
):
    letter = db.get(Letter, letter_id)
    if not letter or letter.status != "active":
        raise HTTPException(status_code=404, detail="Letter not found")

    blob = blob_container.download_blob(letter.blob_path)
    cipher = blob.readall()
    iv = base64.b64decode(letter.iv_b64)
    tag = base64.b64decode(letter.tag_b64)
    plain = aes_decrypt(cipher, iv, tag)

    preview_text = None
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(plain)
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        preview_text = reader.pages[0].extract_text() or "[No extractable text]"
    except Exception:
        preview_text = "[Preview failed]"
    finally:
        os.remove(tmp_path)

    log_action(db, letter_id, None, "preview", request)
    return JSONResponse({"id": letter.id, "preview": preview_text})

# -----------------------------
# Verify by Token
# -----------------------------
@router.get("/verify/{token}")
def verify_by_token(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow().replace(tzinfo=None)

    vt = db.query(VerificationToken).filter(
        VerificationToken.token == token,
        VerificationToken.expires_at > now,
        VerificationToken.used == False
    ).first()
    if not vt:
        return {"valid": False, "status": "invalid"}

    letter = db.get(Letter, vt.letter_id)
    if not letter:
        return {"valid": False, "status": "invalid"}

    # Expired / revoked handling
    if letter.status == "revoked":
        return {
            "valid": False, "status": "revoked",
            "letter_id": letter.id,
            "hash_prefix": hash_prefix(letter.sha256),
            "sender": (letter.sender.email if letter.sender else None),
            "created_at": letter.created_at.isoformat(),
            "expires_at": letter.expires_at.isoformat() if letter.expires_at else None,
        }
    if letter.expires_at and letter.expires_at.replace(tzinfo=None) < now:
        letter.status = "expired"
        db.commit()
        return {
            "valid": False, "status": "expired",
            "letter_id": letter.id,
            "hash_prefix": hash_prefix(letter.sha256),
            "sender": (letter.sender.email if letter.sender else None),
            "created_at": letter.created_at.isoformat(),
            "expires_at": letter.expires_at.isoformat() if letter.expires_at else None,
        }

    if letter.status != "active":
        return {"valid": False, "status": "invalid"}

    log_action(db, letter.id, None, "verify_ok", request)
    return {
        "valid": True,
        "status": letter.status,
        "letter_id": letter.id,
        "hash_prefix": hash_prefix(letter.sha256),
        "sender": (letter.sender.email if letter.sender else None),
        "created_at": letter.created_at.isoformat(),
        "expires_at": letter.expires_at.isoformat() if letter.expires_at else None,
    }

# -----------------------------
# Revoke
# -----------------------------
def _do_revoke(letter_id: str, payload, db: Session, request: Request):
    letter = db.get(Letter, letter_id)
    if not letter:
        raise HTTPException(status_code=404, detail="Not found")
    if payload["role"] == "staff" and payload["sub"] != letter.sender_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    letter.status = "revoked"
    db.commit()
    log_action(db, letter_id, payload["sub"], "revoke", request)
    if letter.recipient:
        notify_recipient_revoked(letter.recipient.email, letter.id, letter.recipient.phone_number)

    return {"id": letter_id, "status": "revoked"}

@router.post("/{letter_id}/revoke")
def revoke_letter_post(letter_id: str, request: Request,
                       payload = Depends(require_any("staff","admin")),
                       db: Session = Depends(get_db)):
    return _do_revoke(letter_id, payload, db, request)

@router.patch("/{letter_id}/revoke")
def revoke_letter_patch(letter_id: str, request: Request,
                        payload = Depends(require_any("staff","admin")),
                        db: Session = Depends(get_db)):
    return _do_revoke(letter_id, payload, db, request)
