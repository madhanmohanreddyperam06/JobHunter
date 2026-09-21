from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Resume display name")
    description: Optional[str] = Field(None, description="Optional notes or targeted role")


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="Resume display name")
    description: Optional[str] = Field(None, description="Optional notes or targeted role")


class ResumeApplicationSummary(BaseModel):
    """Compact summary of a resume version attached to an application."""
    id: int
    name: str
    version: str
    file_name: Optional[str] = None
    is_active: bool = False

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    id: int
    user_id: int
    parent_id: Optional[int] = None
    name: str
    version: str
    file_name: Optional[str] = None
    file_size: int = 0
    mime_type: str = "application/pdf"
    is_active: bool = False
    description: Optional[str] = None
    application_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListResponse(BaseModel):
    items: List[ResumeResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
