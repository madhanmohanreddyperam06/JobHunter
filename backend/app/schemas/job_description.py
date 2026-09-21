from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.job_description import EMPLOYMENT_TYPES, WORK_ARRANGEMENTS
from app.schemas.job_description_skill import JobDescriptionSkillResponse


class JobDescriptionBase(BaseModel):
    application_id: int = Field(..., description="Application ID this JD links to (1-to-1)")
    title: str = Field(..., min_length=1, max_length=150, description="Job title / role name")
    company_name: str = Field(..., min_length=1, max_length=150, description="Hiring organization name")
    job_url: Optional[str] = Field(None, max_length=500, description="Original posting URL")
    location: Optional[str] = Field(None, max_length=150, description="Job location")
    employment_type: str = Field(default="FULL_TIME", description="Employment type (FULL_TIME, CONTRACT, etc.)")
    work_arrangement: str = Field(default="HYBRID", description="Work arrangement (ONSITE, HYBRID, REMOTE, UNKNOWN)")
    salary: Optional[Union[str, int, float]] = Field(None, description="Compensation / salary range")
    experience_required: Optional[str] = Field(None, max_length=100, description="Experience requirement")

    # Section-separated text
    description: Optional[str] = Field(None, description="General job summary")
    responsibilities: Optional[str] = Field(None, description="Key duties and day-to-day responsibilities")
    requirements: Optional[str] = Field(None, description="Core technical/professional requirements")
    qualifications: Optional[str] = Field(None, description="Preferred qualifications or education")
    benefits: Optional[str] = Field(None, description="Perks, benefits, healthcare, 401k, etc.")

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> str:
        if v is None:
            return "FULL_TIME"
        normalized = v.strip().upper()
        if normalized not in EMPLOYMENT_TYPES:
            raise ValueError(
                f"Invalid employment_type '{v}'. Allowed types: {', '.join(EMPLOYMENT_TYPES)}"
            )
        return normalized

    @field_validator("work_arrangement")
    @classmethod
    def validate_work_arrangement(cls, v: Optional[str]) -> str:
        if v is None:
            return "HYBRID"
        normalized = v.strip().upper()
        if normalized not in WORK_ARRANGEMENTS:
            raise ValueError(
                f"Invalid work_arrangement '{v}'. Allowed arrangements: {', '.join(WORK_ARRANGEMENTS)}"
            )
        return normalized

    @field_validator("salary", mode="before")
    @classmethod
    def normalize_salary(cls, v: Optional[Union[str, int, float]]) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


class JobDescriptionCreate(JobDescriptionBase):
    pass


class JobDescriptionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    company_name: Optional[str] = Field(None, min_length=1, max_length=150)
    job_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=150)
    employment_type: Optional[str] = None
    work_arrangement: Optional[str] = None
    salary: Optional[Union[str, int, float]] = None
    experience_required: Optional[str] = Field(None, max_length=100)

    description: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    qualifications: Optional[str] = None
    benefits: Optional[str] = None

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in EMPLOYMENT_TYPES:
            raise ValueError(
                f"Invalid employment_type '{v}'. Allowed types: {', '.join(EMPLOYMENT_TYPES)}"
            )
        return normalized

    @field_validator("work_arrangement")
    @classmethod
    def validate_work_arrangement(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in WORK_ARRANGEMENTS:
            raise ValueError(
                f"Invalid work_arrangement '{v}'. Allowed arrangements: {', '.join(WORK_ARRANGEMENTS)}"
            )
        return normalized

    @field_validator("salary", mode="before")
    @classmethod
    def normalize_salary(cls, v: Optional[Union[str, int, float]]) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


class JobDescriptionApplicationSummary(BaseModel):
    """Application summary context returned alongside a job description."""
    id: int
    job_title: str
    company_name: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionResponse(BaseModel):
    id: int
    user_id: int
    application_id: int
    title: str
    company_name: str
    job_url: Optional[str] = None
    location: Optional[str] = None
    employment_type: str
    work_arrangement: str
    salary: Optional[str] = None
    experience_required: Optional[str] = None

    description: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    qualifications: Optional[str] = None
    benefits: Optional[str] = None

    captured_at: datetime
    created_at: datetime
    updated_at: datetime

    application: Optional[JobDescriptionApplicationSummary] = None
    skill_count: int = 0
    required_skill_count: int = 0
    preferred_skill_count: int = 0
    skills: List[JobDescriptionSkillResponse] = []

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionListResponse(BaseModel):
    items: List[JobDescriptionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
