"""
ApplicationService layer.
Encapsulates database queries and business rules for job applications,
including user-ownership enforcement, company auto-resolution,
filtering, search, sorting, and pagination.
"""
import math
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload

from fastapi import HTTPException, status as http_status
from app.models.application import Application
from app.models.company import Company
from app.models.resume import Resume
from app.models.application_skill import ApplicationSkill
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_company(self, name: str) -> Company:
        """
        Look up an existing company by name (case-insensitive) or create a new one.
        Ensures companies are not duplicated unnecessarily.
        """
        normalized_name = name.strip()
        stmt = select(Company).where(func.lower(Company.name) == normalized_name.lower())
        company = self.db.execute(stmt).scalars().first()
        if not company:
            company = Company(name=normalized_name)
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
        return company

    def list_applications(
        self,
        user_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        location: Optional[str] = None,
        sort_by: str = "applied_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Application], int, int]:
        """
        List applications belonging strictly to user_id with search, filter,
        sorting, and pagination.
        Returns: (items, total_count, total_pages)
        """
        # Base query with eager loading of company and attached resume
        query = (
            select(Application)
            .join(Application.company)
            .options(
                joinedload(Application.company),
                joinedload(Application.resume),
                joinedload(Application.saved_job_description),
                selectinload(Application.application_skills).joinedload(ApplicationSkill.skill),
            )
            .where(Application.user_id == user_id)
        )

        count_query = (
            select(func.count(Application.id))
            .join(Application.company)
            .where(Application.user_id == user_id)
        )

        # Status filter
        if status and status.strip():
            query = query.where(Application.status == status.strip().upper())
            count_query = count_query.where(Application.status == status.strip().upper())

        # Location filter
        if location and location.strip():
            loc_term = f"%{location.strip().lower()}%"
            query = query.where(func.lower(Application.location).like(loc_term))
            count_query = count_query.where(func.lower(Application.location).like(loc_term))

        # Full-text / substring search across title, company name, and location
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            search_clause = or_(
                func.lower(Application.job_title).like(term),
                func.lower(Company.name).like(term),
                func.lower(Application.location).like(term),
            )
            query = query.where(search_clause)
            count_query = count_query.where(search_clause)

        # Execute total count
        total = self.db.execute(count_query).scalar() or 0

        # Whitelist sorting fields
        sort_mapping = {
            "applied_date": Application.applied_date,
            "created_at": Application.created_at,
            "job_title": Application.job_title,
            "status": Application.status,
            "company": Company.name,
        }

        sort_col = sort_mapping.get(sort_by.lower().strip() if sort_by else "applied_date", Application.applied_date)
        is_desc = (sort_order.lower().strip() == "desc") if sort_order else True

        if is_desc:
            query = query.order_by(desc(sort_col), desc(Application.id))
        else:
            query = query.order_by(asc(sort_col), asc(Application.id))

        # Pagination bounds
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        query = query.offset(offset).limit(page_size)
        items = list(self.db.execute(query).scalars().all())

        return items, total, total_pages

    def get_application(self, user_id: int, application_id: int) -> Optional[Application]:
        """
        Retrieve a single application strictly scoped to the owner user_id.
        Returns None if not found or owned by another user.
        """
        stmt = (
            select(Application)
            .options(
                joinedload(Application.company),
                joinedload(Application.resume),
                joinedload(Application.saved_job_description),
                selectinload(Application.application_skills).joinedload(ApplicationSkill.skill),
            )
            .where(Application.id == application_id, Application.user_id == user_id)
        )
        return self.db.execute(stmt).scalars().first()

    def create_application(self, user_id: int, app_in: ApplicationCreate) -> Application:
        """
        Create a new application for user_id, auto-resolving company by name.
        Validates resume ownership if resume_id is provided.
        """
        company = self.get_or_create_company(app_in.company_name)

        if app_in.resume_id is not None:
            resume = (
                self.db.execute(
                    select(Resume).where(Resume.id == app_in.resume_id, Resume.user_id == user_id)
                )
                .scalars()
                .first()
            )
            if not resume:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Resume not found",
                )

        new_app = Application(
            user_id=user_id,
            company_id=company.id,
            job_title=app_in.job_title.strip(),
            location=app_in.location.strip() if app_in.location else None,
            job_url=app_in.job_url.strip() if app_in.job_url else None,
            salary=app_in.salary,
            employment_type=app_in.employment_type.strip() if app_in.employment_type else None,
            status=app_in.status,
            job_description=app_in.job_description,
            applied_date=app_in.applied_date,
            resume_id=app_in.resume_id,
        )
        self.db.add(new_app)
        self.db.commit()
        self.db.refresh(new_app)
        return self.get_application(user_id, new_app.id)

    def update_application(
        self, user_id: int, application_id: int, app_in: ApplicationUpdate
    ) -> Optional[Application]:
        """
        Update an application scoped to user_id. Returns None if not found.
        Validates resume ownership if resume_id is provided.
        """
        app = self.get_application(user_id, application_id)
        if not app:
            return None

        update_data = app_in.model_dump(exclude_unset=True)

        # Handle company name update if provided
        if "company_name" in update_data and update_data["company_name"]:
            company = self.get_or_create_company(update_data["company_name"])
            app.company_id = company.id

        # Handle resume_id update and validation
        if "resume_id" in update_data:
            resume_id = update_data["resume_id"]
            if resume_id is not None:
                resume = (
                    self.db.execute(
                        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
                    )
                    .scalars()
                    .first()
                )
                if not resume:
                    raise HTTPException(
                        status_code=http_status.HTTP_404_NOT_FOUND,
                        detail="Resume not found",
                    )
            app.resume_id = resume_id

        # Update remaining fields
        for field in [
            "job_title", "location", "job_url", "salary",
            "employment_type", "status", "job_description", "applied_date"
        ]:
            if field in update_data:
                setattr(app, field, update_data[field])

        self.db.commit()
        self.db.refresh(app)
        return self.get_application(user_id, app.id)

    def update_application_status(
        self, user_id: int, application_id: int, status: str
    ) -> Optional[Application]:
        """
        Update only the pipeline status of an application scoped to user_id.
        """
        app = self.get_application(user_id, application_id)
        if not app:
            return None

        app.status = status
        self.db.commit()
        self.db.refresh(app)
        return self.get_application(user_id, app.id)

    def delete_application(self, user_id: int, application_id: int) -> bool:
        """
        Delete an application scoped to user_id. Returns True if deleted, False if not found.
        """
        app = self.get_application(user_id, application_id)
        if not app:
            return False

        self.db.delete(app)
        self.db.commit()
        return True
