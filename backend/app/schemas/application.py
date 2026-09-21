from datetime import datetime, date
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.application import APPLICATION_STATUSES
from app.schemas.company import CompanyResponse
from app.schemas.resume import ResumeApplicationSummary
from app.schemas.application_skill import ApplicationSkillResponse


class ApplicationBase(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=150, description="Role or job title")
    location: Optional[str] = Field(None, max_length=150)
    job_url: Optional[str] = Field(None, max_length=500)
    salary: Optional[Union[str, int, float]] = Field(None, description="Compensation amount or range")
    employment_type: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="SAVED", description="Application status")
    job_description: Optional[str] = None
    applied_date: Optional[date] = None
    resume_id: Optional[int] = Field(None, description="Optional attached resume ID")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v is None:
            return "SAVED"
        normalized = v.strip().upper()
        if normalized not in APPLICATION_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed statuses: {', '.join(APPLICATION_STATUSES)}"
            )
        return normalized

    @field_validator("salary", mode="before")
    @classmethod
    def normalize_salary(cls, v: Optional[Union[str, int, float]]) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


class ApplicationCreate(ApplicationBase):
    company_name: str = Field(..., min_length=1, max_length=150, description="Employer / organization name")


class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=150)
    job_title: Optional[str] = Field(None, min_length=1, max_length=150)
    location: Optional[str] = Field(None, max_length=150)
    job_url: Optional[str] = Field(None, max_length=500)
    salary: Optional[Union[str, int, float]] = None
    employment_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    job_description: Optional[str] = None
    applied_date: Optional[date] = None
    resume_id: Optional[int] = Field(None, description="Optional attached resume ID")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in APPLICATION_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed statuses: {', '.join(APPLICATION_STATUSES)}"
            )
        return normalized

    @field_validator("salary", mode="before")
    @classmethod
    def normalize_salary(cls, v: Optional[Union[str, int, float]]) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., description="New pipeline status")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        normalized = v.strip().upper()
        if normalized not in APPLICATION_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed statuses: {', '.join(APPLICATION_STATUSES)}"
            )
        return normalized


class ApplicationResponse(BaseModel):
    id: int
    company: CompanyResponse
    job_title: str
    location: Optional[str] = None
    job_url: Optional[str] = None
    salary: Optional[str] = None
    employment_type: Optional[str] = None
    status: str
    job_description: Optional[str] = None
    applied_date: Optional[date] = None
    resume_id: Optional[int] = None
    resume: Optional[ResumeApplicationSummary] = None
    has_job_description: bool = False
    job_description_id: Optional[int] = None
    skill_count: int = 0
    primary_skill_count: int = 0
    skills: List[ApplicationSkillResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
