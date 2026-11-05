# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Database Engine & Session Management (SQLite / Supabase PostgreSQL)
# ==============================================================================

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to local SQLite database in workspace root if DATABASE_URL is not set
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = WORKSPACE_ROOT / "cypher_label_guard.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Ensure postgresql:// scheme is used for SQLAlchemy compatibility (Supabase support)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure SQLite engine with thread check disabled for multi-worker FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides an isolated database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
