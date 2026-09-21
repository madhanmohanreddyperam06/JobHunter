from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.application import Application

TASK_PRIORITIES = ("LOW", "MEDIUM", "HIGH", "URGENT")
TASK_STATUSES = ("TODO", "IN_PROGRESS", "COMPLETED", "CANCELLED")


class Task(Base):
    """
    Task action items, deadlines, coding tests, and follow-ups.
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        SQLEnum(*TASK_PRIORITIES, name="task_priority_enum"),
        default="MEDIUM",
        nullable=False
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(*TASK_STATUSES, name="task_status_enum"),
        default="TODO",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="tasks")

    @property
    def job_title(self) -> Optional[str]:
        return self.application.job_title if self.application else None

    @property
    def company_name(self) -> Optional[str]:
        if self.application and self.application.company:
            return self.application.company.name
        return None

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        if self.status in ("COMPLETED", "CANCELLED"):
            return False
        return self.due_date < datetime.utcnow()
