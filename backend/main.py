import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# ==========================================
# Load environment variables
# ==========================================
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
    else:
        print("Warning: .env not found at root — relying on system environment variables.")
except Exception as e:
    print(f"Error loading .env: {e}")

# ==========================================
# Logging configuration
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docchain")
logger.info("DocChain backend initialized")

# ==========================================
# Import internal modules
# ==========================================
from . import scheduler
from .auth import router as auth_router
from .letters import router as letters_router
from .recipients import router as recipients_router
from .admin import router as admin_router
from .database import get_db
from .models import User
from .schemas import MeOut
from .utils import require_auth

# ==========================================
# FastAPI App
# ==========================================
app = FastAPI(title="DocChain Backend")

# ==========================================
# CORS Configuration
# ==========================================
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Routers (prefixed with /api)
# ==========================================
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(letters_router, prefix="/api/letters", tags=["letters"])
app.include_router(recipients_router, prefix="/api", tags=["recipients"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

# ==========================================
# Health Check
# ==========================================
@app.get("/api/healthz_docchain")
def healthz_docchain():
    return {"service": "docchain-backend", "status": "ok"}

# ==========================================
# /me Endpoint
# ==========================================
@app.get("/api/me", response_model=MeOut)
def me_alias(payload=Depends(require_auth), db: Session = Depends(get_db)):
    user = db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return MeOut(
        id=user.id,
        email=user.email,
        role=user.role,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
    )

# ==========================================
# Serve Frontend (Static Files)
# ==========================================
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Frontend mounted from: {frontend_dir}")
else:
    logger.warning("Frontend directory not found; static files not served.")

# ==========================================
# Local Run (optional)
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
