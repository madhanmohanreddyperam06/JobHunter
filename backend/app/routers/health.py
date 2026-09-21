from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.database import get_db
from app.schemas.common import HealthResponse, DatabaseHealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="API Health Check")
def health_check() -> HealthResponse:
    """
    Returns general backend operational status.
    """
    return HealthResponse(
        status="healthy",
        service="job-command-center-api"
    )


@router.get("/database", response_model=DatabaseHealthResponse, summary="Database Connectivity Health Check")
def database_health_check(db: Session = Depends(get_db)) -> DatabaseHealthResponse:
    """
    Executes a query against the MySQL 8 database to verify real-time connectivity.
    Returns HTTP 503 Service Unavailable if the database cannot be reached.
    """
    try:
        # Perform low-overhead roundtrip verification query
        db.execute(text("SELECT 1"))
        return DatabaseHealthResponse(
            status="healthy",
            database="connected"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(exc)}"
        )
