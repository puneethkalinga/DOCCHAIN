import uuid, enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class LetterStatus(enum.Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(
        Enum("admin", "staff", "recipient", name="role_enum"),
        nullable=False,
        default="recipient"
    )
    mfa_enabled = Column(Boolean, default=True)
    phone_number = Column(String, nullable=True)
    last_otp = Column(String, nullable=True)
    last_otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 🔹 Admin-control fields
    upload_enabled = Column(Boolean, default=True)   # Can this user upload letters?
    is_active = Column(Boolean, default=True)        # Soft disable account (false = revoked)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship back to User
    user = relationship("User", backref="refresh_tokens")


class Letter(Base):
    __tablename__ = "letters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_user_id = Column(String, ForeignKey("users.id"))
    recipient_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    sha256 = Column(String, nullable=True)

    file_name_original = Column(Text, nullable=True)
    blob_path = Column(Text, nullable=True)
    iv_b64 = Column(Text, nullable=True)
    tag_b64 = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    sensitivity = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_user_id])
    recipient = relationship("User", foreign_keys=[recipient_user_id])


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    letter_id = Column(String, ForeignKey("letters.id"), nullable=False)
    token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    letter = relationship("Letter", foreign_keys=[letter_id])


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    letter_id = Column(String, ForeignKey("letters.id"))
    actor_user_id = Column(String, ForeignKey("users.id"))
    action = Column(String)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)

    actor = relationship("User", foreign_keys=[actor_user_id])
    letter = relationship("Letter", foreign_keys=[letter_id])
