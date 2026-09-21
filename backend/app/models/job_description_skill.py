from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.job_description import JobDescription
    from app.models.skill import Skill

IMPORTANCE_LEVELS = (
    "REQUIRED",
    "PREFERRED",
)

SOURCE_SECTIONS = (
    "DESCRIPTION",
    "RESPONSIBILITIES",
    "REQUIREMENTS",
    "QUALIFICATIONS",
    "BENEFITS",
    "OTHER",
)


class JobDescriptionSkill(Base):
    """
    Association entity connecting job descriptions to required and preferred skills
    with source section provenance.
    """
    __tablename__ = "job_description_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    job_description_id: Mapped[int] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    importance: Mapped[str] = mapped_column(
        String(50), default="REQUIRED", nullable=False
    )
    source_section: Mapped[str] = mapped_column(
        String(50), default="REQUIREMENTS", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    job_description: Mapped["JobDescription"] = relationship(
        "JobDescription", back_populates="job_description_skills"
    )
    skill: Mapped["Skill"] = relationship(
        "Skill", back_populates="job_description_skills"
    )

    __table_args__ = (
        UniqueConstraint("job_description_id", "skill_id", name="uq_jd_skill"),
    )

    @property
    def skill_name(self) -> str:
        return self.skill.name if self.skill else ""

    @property
    def category(self) -> str:
        return self.skill.category if self.skill else ""
