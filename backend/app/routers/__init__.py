"""
FastAPI route modules for Job Application Command Center.
"""
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.applications import router as applications_router
from app.routers.interviews import router as interviews_router
from app.routers.tasks import router as tasks_router
from app.routers.resumes import router as resumes_router
from app.routers.job_descriptions import router as job_descriptions_router
from app.routers.analytics import router as analytics_router
from app.routers.skills import router as skills_router

__all__ = [
    "health_router",
    "auth_router",
    "applications_router",
    "interviews_router",
    "tasks_router",
    "resumes_router",
    "job_descriptions_router",
    "analytics_router",
    "skills_router",
]
