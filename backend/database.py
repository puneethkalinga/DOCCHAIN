import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ==========================================
# Load environment variables (root-level .env)
# ==========================================
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(BASE_DIR, ".env")
    # Only load local .env if we are not running on Azure
    if "WEBSITE_INSTANCE_ID" not in os.environ and os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
    else:
        print("Running on Azure or env not found at root — relying on system environment variables.")
except Exception as e:
    print(f"Error loading .env: {e}")

# ==========================================
# Database Configuration
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./docchain.db")

is_sqlite = DATABASE_URL.startswith("sqlite")
is_pg = DATABASE_URL.startswith(("postgresql+psycopg", "postgresql://"))

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}
elif is_pg:
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }

# ==========================================
# Create SQLAlchemy Engine
# ==========================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args
)

# ==========================================
# Session Factory
# ==========================================
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

# ==========================================
# Base ORM Class
# ==========================================
Base = declarative_base()

# ==========================================
# Dependency for FastAPI Routes
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
