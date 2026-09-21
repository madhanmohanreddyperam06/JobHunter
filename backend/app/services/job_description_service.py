"""
JobDescriptionService layer.
Encapsulates database operations, 1-to-1 application relationship enforcement,
search, filtering, pagination, sorting, and user-ownership isolation.
"""
import logging
import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.application import Application
from app.models.job_description import JobDescription
from app.models.job_description_skill import JobDescriptionSkill
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionUpdate

logger = logging.getLogger("uvicorn.error")

SORT_FIELDS = {
    "captured_at": JobDescription.captured_at,
    "created_at": JobDescription.created_at,
    "updated_at": JobDescription.updated_at,
    "title": JobDescription.title,
    "company_name": JobDescription.company_name,
}


class JobDescriptionService:
    def __init__(self, db: Session):
        self.db = db

    def list_job_descriptions(
        self,
        user_id: int,
        search: Optional[str] = None,
        employment_type: Optional[str] = None,
        work_arrangement: Optional[str] = None,
        application_id: Optional[int] = None,
        sort_by: str = "captured_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[JobDescription], int, int]:
        """
        Retrieve paginated job descriptions belonging strictly to user_id.
        Supports full-text search across title, company, description, and sections,
        filtering by employment_type, work_arrangement, application_id, and sorting.
        Returns: (items, total_count, total_pages)
        """
        query = (
            select(JobDescription)
            .options(
                joinedload(JobDescription.application).joinedload(Application.company),
                selectinload(JobDescription.job_description_skills).joinedload(JobDescriptionSkill.skill),
            )
            .where(JobDescription.user_id == user_id)
        )

        # Filters
        if application_id is not None:
            query = query.where(JobDescription.application_id == application_id)

        if employment_type:
            query = query.where(JobDescription.employment_type == employment_type.strip().upper())

        if work_arrangement:
            query = query.where(JobDescription.work_arrangement == work_arrangement.strip().upper())

        # Search across all text & section fields
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    JobDescription.title.ilike(search_pattern),
                    JobDescription.company_name.ilike(search_pattern),
                    JobDescription.location.ilike(search_pattern),
                    JobDescription.description.ilike(search_pattern),
                    JobDescription.responsibilities.ilike(search_pattern),
                    JobDescription.requirements.ilike(search_pattern),
                    JobDescription.qualifications.ilike(search_pattern),
                    JobDescription.benefits.ilike(search_pattern),
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        # Sorting
        sort_col = SORT_FIELDS.get(sort_by, JobDescription.captured_at)
        order_fn = asc if sort_order.lower() == "asc" else desc
        query = query.order_by(order_fn(sort_col), desc(JobDescription.id))

        # Pagination
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size
        items = self.db.execute(query.offset(offset).limit(page_size)).scalars().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return list(items), total, total_pages

    def get_job_description(self, user_id: int, jd_id: int) -> Optional[JobDescription]:
        """
        Retrieve a single job description strictly owned by user_id.
        """
        stmt = (
            select(JobDescription)
            .options(
                joinedload(JobDescription.application).joinedload(Application.company),
                selectinload(JobDescription.job_description_skills).joinedload(JobDescriptionSkill.skill),
            )
            .where(JobDescription.id == jd_id, JobDescription.user_id == user_id)
        )
        return self.db.execute(stmt).scalars().first()

    def get_by_application_id(self, user_id: int, application_id: int) -> Optional[JobDescription]:
        """
        Retrieve a job description linked to a specific application owned by user_id.
        """
        stmt = (
            select(JobDescription)
            .options(
                joinedload(JobDescription.application).joinedload(Application.company),
                selectinload(JobDescription.job_description_skills).joinedload(JobDescriptionSkill.skill),
            )
            .where(
                JobDescription.application_id == application_id,
                JobDescription.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalars().first()

    def create_job_description(
        self, user_id: int, jd_in: JobDescriptionCreate
    ) -> JobDescription:
        """
        Create a job description linked to an application.
        Enforces:
        - Application must exist and be owned by user_id (otherwise 404 / 403)
        - Application cannot already have a job description (1-to-1 constraint -> 409 Conflict)
        - captured_at is automatically recorded and immutable
        """
        # 1. Verify application ownership
        app_stmt = select(Application).where(Application.id == jd_in.application_id)
        app = self.db.execute(app_stmt).scalars().first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {jd_in.application_id} not found.",
            )
        if app.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to attach a job description to this application.",
            )

        # 2. Check 1-to-1 uniqueness
        existing_stmt = select(JobDescription).where(
            JobDescription.application_id == jd_in.application_id
        )
        existing = self.db.execute(existing_stmt).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A job description is already linked to this application. Each application may only have one job description.",
            )

        # 3. Create record
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        new_jd = JobDescription(
            user_id=user_id,
            application_id=jd_in.application_id,
            title=jd_in.title.strip(),
            company_name=jd_in.company_name.strip(),
            job_url=jd_in.job_url.strip() if jd_in.job_url else None,
            location=jd_in.location.strip() if jd_in.location else None,
            employment_type=jd_in.employment_type,
            work_arrangement=jd_in.work_arrangement,
            salary=jd_in.salary,
            experience_required=jd_in.experience_required.strip() if jd_in.experience_required else None,
            description=jd_in.description,
            responsibilities=jd_in.responsibilities,
            requirements=jd_in.requirements,
            qualifications=jd_in.qualifications,
            benefits=jd_in.benefits,
            captured_at=now,
        )
        self.db.add(new_jd)
        self.db.commit()
        self.db.refresh(new_jd)

        return self.get_job_description(user_id, new_jd.id)

    def update_job_description(
        self, user_id: int, jd_id: int, jd_in: JobDescriptionUpdate
    ) -> Optional[JobDescription]:
        """
        Update an existing job description strictly owned by user_id.
        captured_at and application_id are immutable and cannot be updated.
        """
        jd = self.get_job_description(user_id, jd_id)
        if not jd:
            return None

        update_data = jd_in.model_dump(exclude_unset=True)

        # Never permit changing application_id or captured_at
        update_data.pop("application_id", None)
        update_data.pop("captured_at", None)

        for field, value in update_data.items():
            if field in ("title", "company_name") and value is not None:
                setattr(jd, field, value.strip())
            elif field in ("job_url", "location", "experience_required") and value is not None:
                setattr(jd, field, value.strip() if isinstance(value, str) else value)
            else:
                setattr(jd, field, value)

        self.db.commit()
        self.db.refresh(jd)
        return self.get_job_description(user_id, jd.id)

    def delete_job_description(self, user_id: int, jd_id: int) -> bool:
        """
        Delete a job description strictly owned by user_id.
        The associated Application is preserved intact.
        """
        jd = self.get_job_description(user_id, jd_id)
        if not jd:
            return False

        self.db.delete(jd)
        self.db.commit()
        return True
