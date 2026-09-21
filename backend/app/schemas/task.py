from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_TASK_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}
VALID_TASK_STATUSES = {"TODO", "IN_PROGRESS", "COMPLETED", "CANCELLED"}


class TaskApplicationSummary(BaseModel):
    """Condensed application information embedded within task responses."""
    id: int
    job_title: str
    company_name: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title or action summary")
    description: Optional[str] = Field(default=None, description="Detailed notes, links, or instructions")
    priority: str = Field(default="MEDIUM", description="Task priority (LOW, MEDIUM, HIGH, URGENT)")
    due_date: Optional[datetime] = Field(default=None, description="Target completion deadline")
    status: str = Field(default="TODO", description="Task status (TODO, IN_PROGRESS, COMPLETED, CANCELLED)")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        if not v:
            return "MEDIUM"
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_PRIORITIES))}")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if not v:
            return "TODO"
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_STATUSES))}")
        return normalized


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title or action summary")
    description: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    due_date: Optional[datetime] = None
    status: Optional[str] = "TODO"
    application_id: Optional[int] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        if not v:
            return "MEDIUM"
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_PRIORITIES))}")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if not v:
            return "TODO"
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_STATUSES))}")
        return normalized


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    application_id: Optional[int] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_PRIORITIES))}")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_STATUSES))}")
        return normalized


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., description="New status for the task")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if not v:
            raise ValueError("Status cannot be empty")
        normalized = v.strip().upper()
        if normalized not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values are: {', '.join(sorted(VALID_TASK_STATUSES))}")
        return normalized


class TaskResponse(BaseModel):
    id: int
    user_id: int
    application_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Associated application & company details
    application: Optional[TaskApplicationSummary] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskSummaryResponse(BaseModel):
    total: int
    pending: int
    due_today: int
    overdue: int
    completed: int
