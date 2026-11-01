import os
import smtplib
import traceback
from email.mime.text import MIMEText
from twilio.rest import Client

# -----------------------------
# Phone Normalizer
# -----------------------------
DEFAULT_CC = os.getenv("DEFAULT_CC", "+91")

def normalize_phone(number: str, default_cc: str = DEFAULT_CC) -> str:
    """
    Normalize phone number to E.164 format.
    - If it already starts with '+', return as-is.
    - If it starts with '0', strip leading 0 and add default country code.
    - Otherwise, prepend default country code.
    """
    if not number:
        return None
    number = number.strip().replace(" ", "")
    if number.startswith("+"):
        return number
    if number.startswith("0"):
        number = number.lstrip("0")
    return f"{default_cc}{number}"

# -----------------------------
# Base Email Sender
# -----------------------------
def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = to_email

        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            server.sendmail(os.getenv("EMAIL_FROM"), [to_email], msg.as_string())

        print(f"[Email] Sent to {to_email}: {subject}")
    except Exception as e:
        print(f"[Email Error] {e}")
        traceback.print_exc()

# -----------------------------
# Base SMS Sender (Twilio)
# -----------------------------
def send_sms(to_number: str, body: str):
    try:
        norm_number = normalize_phone(to_number)
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        client.messages.create(
            body=body,
            from_=os.getenv("TWILIO_FROM"),
            to=norm_number
        )
        print(f"[SMS] Sent to {norm_number}: {body}")
    except Exception as e:
        print(f"[SMS Error] {e}")
        traceback.print_exc()

# -----------------------------
# Notification Helpers
# -----------------------------
def notify_recipient_new_letter(recipient_email: str, letter_id: str, phone_number: str = None):
    subject = "New Government Letter Issued"
    body = (
        f"Dear {recipient_email},\n\n"
        f"A new letter (ID: {letter_id}) has been securely issued to you.\n\n"
        f"Please log in to DocChain to view it.\n\n"
        f"- DocChain"
    )
    send_email(recipient_email, subject, body)
    if phone_number:
        send_sms(phone_number, f"[DocChain] A new letter (ID: {letter_id}) has been issued to you.")

def notify_recipient_revoked(recipient_email: str, letter_id: str, phone_number: str = None):
    subject = "Letter Revoked"
    body = (
        f"Dear {recipient_email},\n\n"
        f"Letter {letter_id} has been revoked and is no longer accessible.\n\n"
        f"- DocChain"
    )
    send_email(recipient_email, subject, body)
    if phone_number:
        send_sms(phone_number, f"[DocChain] Letter {letter_id} has been revoked.")

def notify_recipient_expired(recipient_email: str, letter_id: str, phone_number: str = None):
    subject = "Letter Expired"
    body = (
        f"Dear {recipient_email},\n\n"
        f"Letter {letter_id} has expired and can no longer be accessed.\n\n"
        f"- DocChain"
    )
    send_email(recipient_email, subject, body)
    if phone_number:
        send_sms(phone_number, f"[DocChain] Letter {letter_id} has expired.")
