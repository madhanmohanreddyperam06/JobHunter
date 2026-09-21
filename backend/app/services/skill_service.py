"""
SkillService layer.
Encapsulates database operations and business logic for:
1. User-owned skill catalog management with duplicate detection (409 Conflict) and deletion guard (409 Conflict).
2. Many-to-many application-skill associations with proficiency and primary priority.
3. Many-to-many job-description-skill associations with importance and section provenance.
4. Skill intelligence statistics and aggregations.
"""
import math
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, desc, asc, distinct
from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException, status as http_status

from app.models.skill import Skill, normalize_skill_name, SKILL_CATEGORIES
from app.models.application import Application
from app.models.application_skill import ApplicationSkill, PROFICIENCY_LEVELS
from app.models.job_description import JobDescription
from app.models.job_description_skill import JobDescriptionSkill, IMPORTANCE_LEVELS, SOURCE_SECTIONS
from app.schemas.skill import (
    SkillCreate, SkillUpdate, SkillStatsResponse
)
from app.schemas.application_skill import (
    ApplicationSkillCreate, ApplicationSkillUpdate
)
from app.schemas.job_description_skill import (
    JobDescriptionSkillCreate, JobDescriptionSkillUpdate
)

SORT_FIELDS = {
    "name": Skill.name,
    "category": Skill.category,
    "created_at": Skill.created_at,
    "updated_at": Skill.updated_at,
}


class SkillService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # 1. Skill Master Catalog CRUD
    # ---------------------------------------------------------

    def list_skills(
        self,
        user_id: int,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Skill], int, int]:
        """
        List skills belonging strictly to user_id with search, category filtering,
        sorting, and pagination.
        Returns: (items, total_count, total_pages)
        """
        query = (
            select(Skill)
            .options(
                selectinload(Skill.application_skills),
                selectinload(Skill.job_description_skills),
            )
            .where(Skill.user_id == user_id)
        )

        count_query = select(func.count(Skill.id)).where(Skill.user_id == user_id)

        if search:
            pattern = f"%{search.strip()}%"
            search_cond = or_(
                Skill.name.ilike(pattern),
                Skill.normalized_name.ilike(pattern),
                Skill.aliases.ilike(pattern),
                Skill.description.ilike(pattern),
            )
            query = query.where(search_cond)
            count_query = count_query.where(search_cond)

        if category:
            cat_upper = category.strip().upper()
            query = query.where(Skill.category == cat_upper)
            count_query = count_query.where(Skill.category == cat_upper)

        total = self.db.execute(count_query).scalar() or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        sort_column = SORT_FIELDS.get(sort_by, Skill.name)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        offset = (max(1, page) - 1) * page_size
        query = query.offset(offset).limit(page_size)

        items = list(self.db.execute(query).scalars().all())
        return items, total, total_pages

    def get_skill(self, user_id: int, skill_id: int) -> Optional[Skill]:
        """
        Retrieve a single skill strictly scoped to user_id.
        """
        stmt = (
            select(Skill)
            .options(
                selectinload(Skill.application_skills),
                selectinload(Skill.job_description_skills),
            )
            .where(Skill.id == skill_id, Skill.user_id == user_id)
        )
        return self.db.execute(stmt).scalars().first()

    def create_skill(self, user_id: int, skill_in: SkillCreate) -> Skill:
        """
        Create a new skill in the catalog.
        Rejects duplicates (case-insensitive and whitespace-normalized) with 409 Conflict.
        """
        normalized = normalize_skill_name(skill_in.name)
        if not normalized:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Skill name cannot be empty or whitespace only.",
            )

        existing = (
            self.db.execute(
                select(Skill).where(
                    Skill.user_id == user_id,
                    Skill.normalized_name == normalized,
                )
            )
            .scalars()
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=f"Skill '{skill_in.name}' already exists in your catalog.",
            )

        skill = Skill(
            user_id=user_id,
            name=skill_in.name.strip(),
            normalized_name=normalized,
            category=skill_in.category,
            description=skill_in.description.strip() if skill_in.description else None,
            aliases=skill_in.aliases.strip() if skill_in.aliases else None,
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def update_skill(self, user_id: int, skill_id: int, skill_in: SkillUpdate) -> Skill:
        """
        Update an existing skill in the user's catalog.
        Prevents duplicate names across other catalog items with 409 Conflict.
        """
        skill = self.get_skill(user_id, skill_id)
        if not skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill not found",
            )

        if skill_in.name is not None:
            new_normalized = normalize_skill_name(skill_in.name)
            if not new_normalized:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Skill name cannot be empty.",
                )
            if new_normalized != skill.normalized_name:
                conflict = (
                    self.db.execute(
                        select(Skill).where(
                            Skill.user_id == user_id,
                            Skill.normalized_name == new_normalized,
                            Skill.id != skill_id,
                        )
                    )
                    .scalars()
                    .first()
                )
                if conflict:
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=f"Another skill named '{skill_in.name}' already exists in your catalog.",
                    )
                skill.name = skill_in.name.strip()
                skill.normalized_name = new_normalized

        if skill_in.category is not None:
            skill.category = skill_in.category

        if skill_in.description is not None:
            skill.description = skill_in.description.strip() if skill_in.description else None

        if skill_in.aliases is not None:
            skill.aliases = skill_in.aliases.strip() if skill_in.aliases else None

        self.db.commit()
        self.db.refresh(skill)
        return skill

    def delete_skill(self, user_id: int, skill_id: int) -> None:
        """
        Delete a skill from the catalog.
        Rejects deletion with 409 Conflict if linked to any applications or job descriptions.
        """
        skill = self.get_skill(user_id, skill_id)
        if not skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill not found",
            )

        app_count = skill.application_count
        jd_count = skill.job_description_count
        if app_count > 0 or jd_count > 0:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot delete skill '{skill.name}' because it is currently linked to "
                    f"{app_count} application(s) and {jd_count} job description(s). "
                    "Unlink it from those records before deleting."
                ),
            )

        self.db.delete(skill)
        self.db.commit()

    def get_skill_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Aggregate skill intelligence stats:
        - total catalog skills
        - distinct skills used in applications
        - distinct skills linked in job descriptions
        - top used skills across all mappings
        - breakdown of skills by category
        """
        total_skills = self.db.execute(
            select(func.count(Skill.id)).where(Skill.user_id == user_id)
        ).scalar() or 0

        # Distinct skills linked to user's applications
        skills_in_apps = self.db.execute(
            select(func.count(distinct(ApplicationSkill.skill_id)))
            .join(Application, Application.id == ApplicationSkill.application_id)
            .where(Application.user_id == user_id)
        ).scalar() or 0

        # Distinct skills linked to user's job descriptions
        skills_in_jds = self.db.execute(
            select(func.count(distinct(JobDescriptionSkill.skill_id)))
            .join(JobDescription, JobDescription.id == JobDescriptionSkill.job_description_id)
            .where(JobDescription.user_id == user_id)
        ).scalar() or 0

        # Category breakdown
        cat_rows = self.db.execute(
            select(Skill.category, func.count(Skill.id))
            .where(Skill.user_id == user_id)
            .group_by(Skill.category)
        ).all()
        category_counts = {cat: count for cat, count in cat_rows}

        # Top used skills
        all_skills = list(
            self.db.execute(
                select(Skill)
                .options(
                    selectinload(Skill.application_skills),
                    selectinload(Skill.job_description_skills),
                )
                .where(Skill.user_id == user_id)
            )
            .scalars()
            .all()
        )

        top_skills = sorted(
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category,
                    "application_count": s.application_count,
                    "job_description_count": s.job_description_count,
                    "total_usage": s.application_count + s.job_description_count,
                }
                for s in all_skills
            ],
            key=lambda x: x["total_usage"],
            reverse=True,
        )[:8]

        return {
            "total_skills": total_skills,
            "skills_in_applications": skills_in_apps,
            "skills_in_job_descriptions": skills_in_jds,
            "top_used_skills": top_skills,
            "category_counts": category_counts,
        }

    # ---------------------------------------------------------
    # 2. Application ↔ Skill Mapping
    # ---------------------------------------------------------

    def _get_user_application(self, user_id: int, application_id: int) -> Application:
        app = self.db.execute(
            select(Application).where(Application.id == application_id, Application.user_id == user_id)
        ).scalars().first()
        if not app:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        return app

    def list_application_skills(self, user_id: int, application_id: int) -> List[ApplicationSkill]:
        """List all skills associated with an application."""
        self._get_user_application(user_id, application_id)
        stmt = (
            select(ApplicationSkill)
            .options(joinedload(ApplicationSkill.skill))
            .where(ApplicationSkill.application_id == application_id)
            .order_by(
                desc(ApplicationSkill.is_primary),
                desc(ApplicationSkill.years_experience),
                asc(ApplicationSkill.created_at),
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def add_application_skill(
        self, user_id: int, application_id: int, data: ApplicationSkillCreate
    ) -> ApplicationSkill:
        """
        Map a skill to an application with proficiency, experience, and priority.
        Validates ownership of both application and skill.
        Rejects duplicates with 409 Conflict.
        """
        self._get_user_application(user_id, application_id)

        skill = self.get_skill(user_id, data.skill_id)
        if not skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill not found in catalog",
            )

        existing = self.db.execute(
            select(ApplicationSkill).where(
                ApplicationSkill.application_id == application_id,
                ApplicationSkill.skill_id == data.skill_id,
            )
        ).scalars().first()
        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=f"Skill '{skill.name}' is already attached to this application.",
            )

        app_skill = ApplicationSkill(
            application_id=application_id,
            skill_id=data.skill_id,
            proficiency=data.proficiency or "UNKNOWN",
            years_experience=data.years_experience,
            is_primary=bool(data.is_primary),
        )
        self.db.add(app_skill)
        self.db.commit()

        # Re-fetch with joined skill
        stmt = (
            select(ApplicationSkill)
            .options(joinedload(ApplicationSkill.skill))
            .where(ApplicationSkill.id == app_skill.id)
        )
        return self.db.execute(stmt).scalars().first()

    def update_application_skill(
        self, user_id: int, application_id: int, skill_id: int, data: ApplicationSkillUpdate
    ) -> ApplicationSkill:
        """Update an application-skill mapping's proficiency, years, or primary status."""
        self._get_user_application(user_id, application_id)

        app_skill = self.db.execute(
            select(ApplicationSkill).where(
                ApplicationSkill.application_id == application_id,
                ApplicationSkill.skill_id == skill_id,
            )
        ).scalars().first()
        if not app_skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill mapping not found on this application",
            )

        if data.proficiency is not None:
            app_skill.proficiency = data.proficiency
        if data.years_experience is not None:
            app_skill.years_experience = data.years_experience
        if data.is_primary is not None:
            app_skill.is_primary = data.is_primary

        self.db.commit()

        stmt = (
            select(ApplicationSkill)
            .options(joinedload(ApplicationSkill.skill))
            .where(ApplicationSkill.id == app_skill.id)
        )
        return self.db.execute(stmt).scalars().first()

    def remove_application_skill(self, user_id: int, application_id: int, skill_id: int) -> None:
        """Remove a skill mapping from an application."""
        self._get_user_application(user_id, application_id)

        app_skill = self.db.execute(
            select(ApplicationSkill).where(
                ApplicationSkill.application_id == application_id,
                ApplicationSkill.skill_id == skill_id,
            )
        ).scalars().first()
        if not app_skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill mapping not found on this application",
            )

        self.db.delete(app_skill)
        self.db.commit()

    # ---------------------------------------------------------
    # 3. Job Description ↔ Skill Mapping
    # ---------------------------------------------------------

    def _get_user_job_description(self, user_id: int, job_description_id: int) -> JobDescription:
        jd = self.db.execute(
            select(JobDescription).where(
                JobDescription.id == job_description_id,
                JobDescription.user_id == user_id,
            )
        ).scalars().first()
        if not jd:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Job description not found",
            )
        return jd

    def list_job_description_skills(
        self, user_id: int, job_description_id: int
    ) -> List[JobDescriptionSkill]:
        """List all skills associated with a job description."""
        self._get_user_job_description(user_id, job_description_id)
        stmt = (
            select(JobDescriptionSkill)
            .options(joinedload(JobDescriptionSkill.skill))
            .where(JobDescriptionSkill.job_description_id == job_description_id)
            .order_by(
                asc(JobDescriptionSkill.importance),
                asc(JobDescriptionSkill.created_at),
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def add_job_description_skill(
        self, user_id: int, job_description_id: int, data: JobDescriptionSkillCreate
    ) -> JobDescriptionSkill:
        """
        Map a skill to a job description with importance and section provenance.
        Validates ownership of both JD and skill.
        Rejects duplicates with 409 Conflict.
        """
        self._get_user_job_description(user_id, job_description_id)

        skill = self.get_skill(user_id, data.skill_id)
        if not skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill not found in catalog",
            )

        existing = self.db.execute(
            select(JobDescriptionSkill).where(
                JobDescriptionSkill.job_description_id == job_description_id,
                JobDescriptionSkill.skill_id == data.skill_id,
            )
        ).scalars().first()
        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=f"Skill '{skill.name}' is already attached to this job description.",
            )

        jd_skill = JobDescriptionSkill(
            job_description_id=job_description_id,
            skill_id=data.skill_id,
            importance=data.importance or "REQUIRED",
            source_section=data.source_section or "REQUIREMENTS",
        )
        self.db.add(jd_skill)
        self.db.commit()

        # Re-fetch with joined skill
        stmt = (
            select(JobDescriptionSkill)
            .options(joinedload(JobDescriptionSkill.skill))
            .where(JobDescriptionSkill.id == jd_skill.id)
        )
        return self.db.execute(stmt).scalars().first()

    def update_job_description_skill(
        self, user_id: int, job_description_id: int, skill_id: int, data: JobDescriptionSkillUpdate
    ) -> JobDescriptionSkill:
        """Update a job-description-skill mapping's importance or source section."""
        self._get_user_job_description(user_id, job_description_id)

        jd_skill = self.db.execute(
            select(JobDescriptionSkill).where(
                JobDescriptionSkill.job_description_id == job_description_id,
                JobDescriptionSkill.skill_id == skill_id,
            )
        ).scalars().first()
        if not jd_skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill mapping not found on this job description",
            )

        if data.importance is not None:
            jd_skill.importance = data.importance
        if data.source_section is not None:
            jd_skill.source_section = data.source_section

        self.db.commit()

        stmt = (
            select(JobDescriptionSkill)
            .options(joinedload(JobDescriptionSkill.skill))
            .where(JobDescriptionSkill.id == jd_skill.id)
        )
        return self.db.execute(stmt).scalars().first()

    def remove_job_description_skill(
        self, user_id: int, job_description_id: int, skill_id: int
    ) -> None:
        """Remove a skill mapping from a job description."""
        self._get_user_job_description(user_id, job_description_id)

        jd_skill = self.db.execute(
            select(JobDescriptionSkill).where(
                JobDescriptionSkill.job_description_id == job_description_id,
                JobDescriptionSkill.skill_id == skill_id,
            )
        ).scalars().first()
        if not jd_skill:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Skill mapping not found on this job description",
            )

        self.db.delete(jd_skill)
        self.db.commit()
