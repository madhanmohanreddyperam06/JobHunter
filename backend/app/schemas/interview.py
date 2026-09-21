from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


VALID_INTERVIEW_STATUSES = {
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED",
    "RESCHEDULED",
    "NO_SHOW"
}

VALID_INTERVIEW_TYPES = {
    "PHONE",
    "VIDEO",
    "ONSITE",
    "TECHNICAL",
    "HR",
    "BEHAVIORAL",
    "MANAGERIAL",
    "OTHER"
}


class InterviewApplicationSummary(BaseModel):
    """Condensed application information embedded within interview responses."""
    id: int
    job_title: str
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class InterviewBase(BaseModel):
    round_name: str = Field(..., min_length=1, max_length=100, description="Interview round name, e.g., Technical Screen")
    interview_type: Optional[str] = Field(default="VIDEO", description="Type of interview round")
    scheduled_at: Optional[datetime] = Field(default=None, description="Scheduled datetime")
    duration_minutes: Optional[int] = Field(default=45, ge=5, le=480, description="Duration in minutes")
    location: Optional[str] = Field(default=None, max_length=255, description="Physical location or conference room")
    meeting_link: Optional[str] = Field(default=None, max_length=500, description="Virtual video meeting URL")
    interviewer: Optional[str] = Field(default=None, max_length=150, description="Name of interviewer or panel")
    interviewer_email: Optional[str] = Field(default=None, max_length=150, description="Email of interviewer")
    status: str = Field(default="SCHEDULED", description="Status of the interview")
    notes: Optional[str] = Field(default=None, description="Preparation or debrief notes")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if not v:
            return "SCHEDULED"
        normalized = v.strip().upper()
        if normalized not in VALID_INTERVIEW_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_INTERVIEW_STATUSES))}")
        return normalized

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return "VIDEO"
        normalized = v.strip().upper()
        # Accept valid types or preserve custom string capitalized
        if normalized in VALID_INTERVIEW_TYPES:
            return normalized
        return v.strip()


class InterviewCreate(BaseModel):
    application_id: int = Field(..., description="ID of the job application this round belongs to")
    round_name: str = Field(..., min_length=1, max_length=100)
    interview_type: Optional[str] = Field(default="VIDEO")
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=45, ge=5, le=480)
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_url: Optional[str] = None
    interviewer: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    status: str = "SCHEDULED"
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: any) -> any:
        if isinstance(data, dict):
            # Map meeting_url -> meeting_link if meeting_link not provided
            if "meeting_url" in data and not data.get("meeting_link"):
                data["meeting_link"] = data["meeting_url"]
            # Map interviewer_name -> interviewer if interviewer not provided
            if "interviewer_name" in data and not data.get("interviewer"):
                data["interviewer"] = data["interviewer_name"]
            # Default round_name if omitted or empty
            if not data.get("round_name"):
                itype = data.get("interview_type") or "Interview"
                data["round_name"] = f"{itype} Round"
        return data

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if not v:
            return "SCHEDULED"
        normalized = v.strip().upper()
        if normalized not in VALID_INTERVIEW_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_INTERVIEW_STATUSES))}")
        return normalized


class InterviewUpdate(BaseModel):
    application_id: Optional[int] = None
    round_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    interview_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_url: Optional[str] = None
    interviewer: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: any) -> any:
        if isinstance(data, dict):
            if "meeting_url" in data and not data.get("meeting_link"):
                data["meeting_link"] = data["meeting_url"]
            if "interviewer_name" in data and not data.get("interviewer"):
                data["interviewer"] = data["interviewer_name"]
        return data

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in VALID_INTERVIEW_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_INTERVIEW_STATUSES))}")
        return normalized


class InterviewStatusUpdate(BaseModel):
    status: str = Field(..., description="New status for the interview")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if not v:
            raise ValueError("Status cannot be empty")
        normalized = v.strip().upper()
        if normalized not in VALID_INTERVIEW_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_INTERVIEW_STATUSES))}")
        return normalized


class InterviewResponse(BaseModel):
    id: int
    application_id: int
    round_name: str
    interview_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = 45
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_url: Optional[str] = None
    interviewer: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Associated application and company details
    application: Optional[InterviewApplicationSummary] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_helpers(cls, data: any) -> any:
        # If data is an ORM object or dict, populate meeting_url and interviewer_name aliases
        if hasattr(data, "meeting_link"):
            link = getattr(data, "meeting_link", None)
            name = getattr(data, "interviewer", None)
            app = getattr(data, "application", None)
            job_title = app.job_title if app else None
            company_name = app.company.name if (app and app.company) else None

            # Return a dict representation if needed or let pydantic read attributes
            # With from_attributes=True, pydantic reads attributes from the ORM object.
            # But we can also set properties dynamically if data is a dict
            pass
        return data


class InterviewListResponse(BaseModel):
    items: List[InterviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
