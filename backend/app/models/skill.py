from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.application_skill import ApplicationSkill
    from app.models.job_description_skill import JobDescriptionSkill

SKILL_CATEGORIES = (
    "PROGRAMMING_LANGUAGE",
    "FRONTEND",
    "BACKEND",
    "DATABASE",
    "CLOUD",
    "DEVOPS",
    "AI_ML",
    "DATA",
    "MOBILE",
    "TESTING",
    "SECURITY",
    "TOOLS",
    "SOFT_SKILL",
    "OTHER",
)


def normalize_skill_name(name: str) -> str:
    """
    Standard skill normalization:
    - Trim whitespace
    - Lowercase
    - Collapse multiple whitespace into a single space
    - Preserves meaningful characters such as '.', '+', '#', '-' (e.g. C++, C#, .NET, Node.js)
    """
    if not name:
        return ""
    return " ".join(name.strip().split()).lower()


class Skill(Base):
    """
    User-owned skill catalog entity representing technical and professional proficiencies.
    Normalized and reusable across Applications and Job Descriptions.
    """
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aliases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="skills")
    application_skills: Mapped[List["ApplicationSkill"]] = relationship(
        "ApplicationSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    job_description_skills: Mapped[List["JobDescriptionSkill"]] = relationship(
        "JobDescriptionSkill", back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name", name="uq_user_skill_normalized"),
    )

    @property
    def application_count(self) -> int:
        try:
            return len(self.application_skills) if self.application_skills is not None else 0
        except Exception:
            return 0

    @property
    def job_description_count(self) -> int:
        try:
            return len(self.job_description_skills) if self.job_description_skills is not None else 0
        except Exception:
            return 0
