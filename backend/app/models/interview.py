from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class Interview(Base):
    """
    Interview round entity associated with a specific job application.
    """
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    round_name: Mapped[str] = mapped_column(String(100), nullable=False)
    interview_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # PHONE, VIDEO, ONSITE, TECHNICAL, HR, BEHAVIORAL
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=45)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    interviewer: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    interviewer_email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", nullable=False)  # SCHEDULED, COMPLETED, CANCELLED, RESCHEDULED, NO_SHOW
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to parent application
    application: Mapped["Application"] = relationship("Application", back_populates="interviews")

    @property
    def meeting_url(self) -> Optional[str]:
        return self.meeting_link

    @property
    def interviewer_name(self) -> Optional[str]:
        return self.interviewer

    @property
    def job_title(self) -> Optional[str]:
        return self.application.job_title if self.application else None

    @property
    def company_name(self) -> Optional[str]:
        if self.application and self.application.company:
            return self.application.company.name
        return None

