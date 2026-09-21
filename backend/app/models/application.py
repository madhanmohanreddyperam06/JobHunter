from datetime import datetime, date
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.company import Company
    from app.models.interview import Interview
    from app.models.task import Task
    from app.models.note import Note
    from app.models.activity_log import ActivityLog
    from app.models.resume import Resume
    from app.models.job_description import JobDescription
    from app.models.application_skill import ApplicationSkill


APPLICATION_STATUSES = (
    "SAVED",
    "APPLIED",
    "ASSESSMENT",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "WITHDRAWN"
)


class Application(Base):
    """
    Core job application record tracked within the command center pipeline.
    """
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    job_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(*APPLICATION_STATUSES, name="application_status_enum"),
        default="SAVED",
        nullable=False,
        index=True
    )
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applied_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resume_id: Mapped[Optional[int]] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    company: Mapped["Company"] = relationship("Company", back_populates="applications")
    resume: Mapped[Optional["Resume"]] = relationship("Resume", back_populates="applications")
    saved_job_description: Mapped[Optional["JobDescription"]] = relationship(
        "JobDescription", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    interviews: Mapped[List["Interview"]] = relationship(
        "Interview", back_populates="application", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="application"
    )
    notes: Mapped[List["Note"]] = relationship(
        "Note", back_populates="application", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="application"
    )
    application_skills: Mapped[List["ApplicationSkill"]] = relationship(
        "ApplicationSkill", back_populates="application", cascade="all, delete-orphan"
    )

    @property
    def company_name(self) -> Optional[str]:
        return self.company.name if self.company else None

    @property
    def company_logo(self) -> Optional[str]:
        return self.company.logo if self.company else None

    @property
    def has_job_description(self) -> bool:
        return self.saved_job_description is not None

    @property
    def job_description_id(self) -> Optional[int]:
        return self.saved_job_description.id if self.saved_job_description else None

    @property
    def skill_count(self) -> int:
        try:
            return len(self.application_skills) if self.application_skills is not None else 0
        except Exception:
            return 0

    @property
    def primary_skill_count(self) -> int:
        try:
            if self.application_skills is None:
                return 0
            return sum(1 for s in self.application_skills if s.is_primary)
        except Exception:
            return 0

    @property
    def skills(self) -> List["ApplicationSkill"]:
        return self.application_skills or []

