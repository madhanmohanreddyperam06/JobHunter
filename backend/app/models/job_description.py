from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.application import Application
    from app.models.job_description_skill import JobDescriptionSkill

EMPLOYMENT_TYPES = (
    "FULL_TIME",
    "PART_TIME",
    "CONTRACT",
    "INTERNSHIP",
    "TEMPORARY",
    "OTHER",
)

WORK_ARRANGEMENTS = (
    "ONSITE",
    "HYBRID",
    "REMOTE",
    "UNKNOWN",
)


class JobDescription(Base):
    """
    Job Description model storing structured, section-separated JD records
    linked 1-to-1 to a job application.
    """
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    job_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    employment_type: Mapped[str] = mapped_column(
        String(50), default="FULL_TIME", nullable=False, index=True
    )
    work_arrangement: Mapped[str] = mapped_column(
        String(50), default="HYBRID", nullable=False, index=True
    )
    salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_required: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Section-separated raw text
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qualifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Immutability: captured_at is set once upon capture and never updated
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_descriptions")
    application: Mapped["Application"] = relationship(
        "Application", back_populates="saved_job_description"
    )
    job_description_skills: Mapped[List["JobDescriptionSkill"]] = relationship(
        "JobDescriptionSkill", back_populates="job_description", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_job_descriptions_user_app", "user_id", "application_id"),
    )

    @property
    def skill_count(self) -> int:
        try:
            return len(self.job_description_skills) if self.job_description_skills is not None else 0
        except Exception:
            return 0

    @property
    def required_skill_count(self) -> int:
        try:
            if self.job_description_skills is None:
                return 0
            return sum(1 for s in self.job_description_skills if s.importance == "REQUIRED")
        except Exception:
            return 0

    @property
    def preferred_skill_count(self) -> int:
        try:
            if self.job_description_skills is None:
                return 0
            return sum(1 for s in self.job_description_skills if s.importance == "PREFERRED")
        except Exception:
            return 0

    @property
    def skills(self) -> List["JobDescriptionSkill"]:
        return self.job_description_skills or []

