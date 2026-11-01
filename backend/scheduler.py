from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from .database import SessionLocal
from .models import Letter
from .notifications import notify_recipient_expired


def expire_letters():
    db = SessionLocal()
    now = datetime.utcnow()
    expired = db.query(Letter).filter(
        Letter.expires_at.isnot(None),
        Letter.expires_at < now,
        Letter.status == "active"
    ).all()

    for letter in expired:
        letter.status = "expired"
        if letter.recipient:
            # 🔔 Notify recipient via email + SMS (if phone_number exists)
            notify_recipient_expired(
                letter.recipient.email,
                letter.id,
                letter.recipient.phone_number
            )

    if expired:
        print(f"[AutoExpiry] Marked {len(expired)} letters as expired at {now}")

    db.commit()
    db.close()


# ------------------------------------------
# 🕒 Background Scheduler (runs every hour)
# ------------------------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(expire_letters, "interval", hours=1)
scheduler.start()

print("Auto-expiry scheduler initialized (interval: 1h)")
