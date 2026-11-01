# create_admin.py
import os, bcrypt, uuid
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from backend.database import Base
from backend.models import User, RefreshToken, Letter, VerificationToken, AccessLog

# Load environment variables from .env
load_dotenv()

# Use Neon DB URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

print("Checking and creating tables...")
Base.metadata.create_all(bind=engine)
print("[OK] Database schema is ready.")

email = "admin@example.com"
password = "Admin#123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
admin_id = str(uuid.uuid4())

try:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (id, email, password_hash, role, mfa_enabled, is_active, upload_enabled)
            VALUES (:id, :email, :password, 'admin', true, true, true)
        """), {"id": admin_id, "email": email, "password": hashed})
    print("[OK] Admin created successfully:", email, password)
except Exception as e:
    if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
        print("[OK] Admin user already exists in the database.")
    else:
        print("[ERROR] Failed to insert admin user:", e)
