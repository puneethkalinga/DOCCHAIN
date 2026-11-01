from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr

UserRole = Literal["admin", "staff", "recipient"]

class SignupIn(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = "recipient"
    mfa_enabled: bool = True
    phone_number: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class VerifyOtpIn(BaseModel):
    email: EmailStr
    otp: str

class MeOut(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    mfa_enabled: bool
    created_at: Optional[datetime] = None
