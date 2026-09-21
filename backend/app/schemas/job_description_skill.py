from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.job_description_skill import IMPORTANCE_LEVELS, SOURCE_SECTIONS
from app.schemas.skill import SkillSummary


class JobDescriptionSkillCreate(BaseModel):
    skill_id: int = Field(..., description="Skill ID from user catalog")
    importance: Optional[str] = Field(default="REQUIRED", description="Importance (REQUIRED or PREFERRED)")
    source_section: Optional[str] = Field(default="REQUIREMENTS", description="Source section in JD")

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v: Optional[str]) -> str:
        if v is None:
            return "REQUIRED"
        normalized = v.strip().upper()
        if normalized not in IMPORTANCE_LEVELS:
            raise ValueError(
                f"Invalid importance '{v}'. Allowed levels: {', '.join(IMPORTANCE_LEVELS)}"
            )
        return normalized

    @field_validator("source_section")
    @classmethod
    def validate_source_section(cls, v: Optional[str]) -> str:
        if v is None:
            return "REQUIREMENTS"
        normalized = v.strip().upper()
        if normalized not in SOURCE_SECTIONS:
            raise ValueError(
                f"Invalid source_section '{v}'. Allowed sections: {', '.join(SOURCE_SECTIONS)}"
            )
        return normalized


class JobDescriptionSkillUpdate(BaseModel):
    importance: Optional[str] = None
    source_section: Optional[str] = None

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in IMPORTANCE_LEVELS:
            raise ValueError(
                f"Invalid importance '{v}'. Allowed levels: {', '.join(IMPORTANCE_LEVELS)}"
            )
        return normalized

    @field_validator("source_section")
    @classmethod
    def validate_source_section(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in SOURCE_SECTIONS:
            raise ValueError(
                f"Invalid source_section '{v}'. Allowed sections: {', '.join(SOURCE_SECTIONS)}"
            )
        return normalized


class JobDescriptionSkillSummary(BaseModel):
    id: int
    job_description_id: int
    skill_id: int
    skill_name: str
    category: str
    importance: str
    source_section: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionSkillResponse(BaseModel):
    id: int
    job_description_id: int
    skill_id: int
    skill_name: str
    category: str
    importance: str
    source_section: str
    created_at: datetime
    skill: Optional[SkillSummary] = None

    model_config = ConfigDict(from_attributes=True)
