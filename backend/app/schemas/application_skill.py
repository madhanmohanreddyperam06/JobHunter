from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.application_skill import PROFICIENCY_LEVELS
from app.schemas.skill import SkillSummary


class ApplicationSkillCreate(BaseModel):
    skill_id: int = Field(..., description="Skill ID from user catalog")
    proficiency: Optional[str] = Field(default="UNKNOWN", description="Proficiency level")
    years_experience: Optional[float] = Field(default=None, ge=0, description="Years of hands-on experience")
    is_primary: Optional[bool] = Field(default=False, description="Whether this is a primary highlight skill")

    @field_validator("proficiency")
    @classmethod
    def validate_proficiency(cls, v: Optional[str]) -> str:
        if v is None:
            return "UNKNOWN"
        normalized = v.strip().upper()
        if normalized not in PROFICIENCY_LEVELS:
            raise ValueError(
                f"Invalid proficiency '{v}'. Allowed levels: {', '.join(PROFICIENCY_LEVELS)}"
            )
        return normalized


class ApplicationSkillUpdate(BaseModel):
    proficiency: Optional[str] = None
    years_experience: Optional[float] = Field(None, ge=0)
    is_primary: Optional[bool] = None

    @field_validator("proficiency")
    @classmethod
    def validate_proficiency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().upper()
        if normalized not in PROFICIENCY_LEVELS:
            raise ValueError(
                f"Invalid proficiency '{v}'. Allowed levels: {', '.join(PROFICIENCY_LEVELS)}"
            )
        return normalized


class ApplicationSkillSummary(BaseModel):
    id: int
    application_id: int
    skill_id: int
    skill_name: str
    category: str
    proficiency: str
    years_experience: Optional[float] = None
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationSkillResponse(BaseModel):
    id: int
    application_id: int
    skill_id: int
    skill_name: str
    category: str
    proficiency: str
    years_experience: Optional[float] = None
    is_primary: bool
    created_at: datetime
    skill: Optional[SkillSummary] = None

    model_config = ConfigDict(from_attributes=True)
