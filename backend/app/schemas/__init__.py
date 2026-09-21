"""
Pydantic v2 validation and serialization schemas.
"""
from app.schemas.common import HealthResponse, DatabaseHealthResponse, MessageResponse
from app.schemas.user import (
    UserBase, UserCreate, UserResponse,
    LoginRequest, Token, TokenData
)
from app.schemas.company import CompanyBase, CompanyCreate, CompanyResponse
from app.schemas.application import (
    ApplicationBase, ApplicationCreate, ApplicationUpdate,
    ApplicationStatusUpdate, ApplicationResponse, ApplicationListResponse
)
from app.schemas.interview import InterviewBase, InterviewCreate, InterviewUpdate, InterviewResponse
from app.schemas.task import TaskBase, TaskCreate, TaskUpdate, TaskResponse
from app.schemas.resume import ResumeBase, ResumeCreate, ResumeResponse
from app.schemas.job_description import (
    JobDescriptionBase, JobDescriptionCreate, JobDescriptionUpdate,
    JobDescriptionResponse, JobDescriptionListResponse, JobDescriptionApplicationSummary
)
from app.schemas.skill import (
    SkillBase, SkillCreate, SkillUpdate, SkillSummary, SkillResponse, SkillListResponse, SkillStatsResponse
)
from app.schemas.application_skill import (
    ApplicationSkillCreate, ApplicationSkillUpdate, ApplicationSkillSummary, ApplicationSkillResponse
)
from app.schemas.job_description_skill import (
    JobDescriptionSkillCreate, JobDescriptionSkillUpdate, JobDescriptionSkillSummary, JobDescriptionSkillResponse
)

__all__ = [
    "HealthResponse",
    "DatabaseHealthResponse",
    "MessageResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "Token",
    "TokenData",
    "CompanyBase",
    "CompanyCreate",
    "CompanyResponse",
    "ApplicationBase",
    "ApplicationCreate",
    "ApplicationUpdate",
    "ApplicationStatusUpdate",
    "ApplicationResponse",
    "ApplicationListResponse",
    "InterviewBase",
    "InterviewCreate",
    "InterviewUpdate",
    "InterviewResponse",
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "ResumeBase",
    "ResumeCreate",
    "ResumeResponse",
    "JobDescriptionBase",
    "JobDescriptionCreate",
    "JobDescriptionUpdate",
    "JobDescriptionResponse",
    "JobDescriptionListResponse",
    "JobDescriptionApplicationSummary",
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillSummary",
    "SkillResponse",
    "SkillListResponse",
    "SkillStatsResponse",
    "ApplicationSkillCreate",
    "ApplicationSkillUpdate",
    "ApplicationSkillSummary",
    "ApplicationSkillResponse",
    "JobDescriptionSkillCreate",
    "JobDescriptionSkillUpdate",
    "JobDescriptionSkillSummary",
    "JobDescriptionSkillResponse",
]
