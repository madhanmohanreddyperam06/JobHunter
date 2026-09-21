from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Float, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.skill import Skill

PROFICIENCY_LEVELS = (
    "BEGINNER",
    "INTERMEDIATE",
    "ADVANCED",
    "EXPERT",
    "UNKNOWN",
)


class ApplicationSkill(Base):
    """
    Association entity connecting applications to candidate proficiencies
    with experience years and primary skill priority.
    """
    __tablename__ = "application_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proficiency: Mapped[str] = mapped_column(
        String(50), default="UNKNOWN", nullable=False
    )
    years_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="application_skills"
    )
    skill: Mapped["Skill"] = relationship(
        "Skill", back_populates="application_skills"
    )

    __table_args__ = (
        UniqueConstraint("application_id", "skill_id", name="uq_application_skill"),
    )

    @property
    def skill_name(self) -> str:
        return self.skill.name if self.skill else ""

    @property
    def category(self) -> str:
        return self.skill.category if self.skill else ""
