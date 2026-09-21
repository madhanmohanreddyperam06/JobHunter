from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.database.base import Base

# SQLAlchemy 2.0 Engine with robust MySQL connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Automatically reconnect if connections go stale
    pool_recycle=3600,       # Recycle connections every hour to match MySQL wait_timeout
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# Database Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Ensures sessions are closed reliably after each request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
