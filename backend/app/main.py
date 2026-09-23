import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.database import engine
from app.database.base import Base

# Import all models to ensure metadata registration before create_all
import app.models  # noqa: F401

from app.routers import (
    health_router,
    auth_router,
    applications_router,
    interviews_router,
    tasks_router,
    resumes_router,
    job_descriptions_router,
    analytics_router,
    skills_router,
)

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Initializes database tables from SQLAlchemy metadata on startup.
    """
    logger.info("Initializing Job Application Command Center Backend...")
    try:
        # Create all tables defined in SQLAlchemy models if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified and initialized successfully.")
    except Exception as exc:
        logger.error("Could not automatically initialize database tables: %s", exc)
    yield
    logger.info("Shutting down Job Application Command Center Backend...")


# Instantiate FastAPI Application
app = FastAPI(
    title="Job Application Command Center API",
    description="Backend REST API and persistence foundation for the Job Application Command Center.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure Explicit CORS for the AngularJS Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
)

# Register All API Routers under /api namespace
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(interviews_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(resumes_router, prefix="/api")
app.include_router(job_descriptions_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(skills_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    """Root redirect message pointing to Swagger documentation."""
    return {
        "title": "Job Application Command Center API",
        "documentation": "/docs",
        "health": "/api/health"
    }
