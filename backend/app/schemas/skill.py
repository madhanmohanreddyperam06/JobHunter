from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.skill import SKILL_CATEGORIES


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Skill name")
    category: str = Field(..., description="Skill classification category")
    description: Optional[str] = Field(None, description="Optional notes or details")
    aliases: Optional[str] = Field(None, description="Comma-separated alternative names or synonyms")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None or not v.strip():
            raise ValueError("Skill name cannot be empty")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v is None:
            raise ValueError("Skill category cannot be empty")
        normalized = v.strip().upper()
        if normalized not in SKILL_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Allowed categories: {', '.join(SKILL_CATEGORIES)}"
            )
        return normalized


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Skill name cannot be empty")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in SKILL_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Allowed categories: {', '.join(SKILL_CATEGORIES)}"
            )
        return normalized


class SkillSummary(BaseModel):
    """Compact skill summary for embedding in relationships and dropdowns."""
    id: int
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class SkillResponse(BaseModel):
    id: int
    user_id: int
    name: str
    normalized_name: str
    category: str
    description: Optional[str] = None
    aliases: Optional[str] = None
    application_count: int = 0
    job_description_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillListResponse(BaseModel):
    items: List[SkillResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class SkillStatsResponse(BaseModel):
    total_skills: int = 0
    skills_in_applications: int = 0
    skills_in_job_descriptions: int = 0
    top_used_skills: List[Dict[str, Any]] = []
    category_counts: Dict[str, int] = {}

    model_config = ConfigDict(from_attributes=True)
