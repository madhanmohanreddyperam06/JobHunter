from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.skill import (
    SkillCreate,
    SkillListResponse,
    SkillResponse,
    SkillStatsResponse,
    SkillUpdate,
)
from app.schemas.application_skill import (
    ApplicationSkillCreate,
    ApplicationSkillResponse,
    ApplicationSkillUpdate,
)
from app.schemas.job_description_skill import (
    JobDescriptionSkillCreate,
    JobDescriptionSkillResponse,
    JobDescriptionSkillUpdate,
)
from app.services.skill_service import SkillService

router = APIRouter(tags=["Skills"])


# =====================================================================
# 1. Skill Master Catalog Endpoints
# =====================================================================

@router.get(
    "/skills",
    response_model=SkillListResponse,
    summary="List Skills Catalog",
    description="Retrieve paginated skills from candidate catalog with search, category filtering, and sorting.",
)
def list_skills(
    search: Optional[str] = Query(None, description="Search term for skill name, aliases, or description"),
    category: Optional[str] = Query(None, description="Filter by skill category"),
    sort_by: str = Query("name", description="Sort field: name, category, created_at, updated_at"),
    sort_order: str = Query("asc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    service = SkillService(db)
    items, total, total_pages = service.list_skills(
        user_id=current_user.id,
        search=search,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return SkillListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "/skills",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Skill",
    description="Add a new skill to candidate catalog. Prevents duplicates (case/whitespace-normalized) with 409 Conflict.",
)
def create_skill(
    skill_in: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillResponse:
    service = SkillService(db)
    return service.create_skill(user_id=current_user.id, skill_in=skill_in)


@router.get(
    "/skills/stats",
    response_model=SkillStatsResponse,
    summary="Get Skill Stats",
    description="Retrieve aggregated statistics including total catalog skills, usage in applications/JDs, and category distribution.",
)
def get_skill_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillStatsResponse:
    service = SkillService(db)
    stats = service.get_skill_stats(user_id=current_user.id)
    return SkillStatsResponse(**stats)


@router.get(
    "/skills/{skill_id}",
    response_model=SkillResponse,
    summary="Get Skill Detail",
    description="Retrieve a single skill record from catalog.",
)
def get_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillResponse:
    service = SkillService(db)
    skill = service.get_skill(user_id=current_user.id, skill_id=skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    return skill


@router.put(
    "/skills/{skill_id}",
    response_model=SkillResponse,
    summary="Update Skill",
    description="Update a skill's name, category, aliases, or description. Enforces duplicate prevention with 409 Conflict.",
)
def update_skill(
    skill_id: int,
    skill_in: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillResponse:
    service = SkillService(db)
    return service.update_skill(user_id=current_user.id, skill_id=skill_id, skill_in=skill_in)


@router.delete(
    "/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Skill",
    description="Delete a skill from catalog. Blocked with 409 Conflict if mapped to any applications or job descriptions.",
)
def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = SkillService(db)
    service.delete_skill(user_id=current_user.id, skill_id=skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =====================================================================
# 2. Application ↔ Skill Mapping Endpoints
# =====================================================================

@router.get(
    "/applications/{application_id}/skills",
    response_model=List[ApplicationSkillResponse],
    summary="List Application Skills",
    description="Retrieve all skills linked to a specific application.",
)
def list_application_skills(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ApplicationSkillResponse]:
    service = SkillService(db)
    return service.list_application_skills(user_id=current_user.id, application_id=application_id)


@router.post(
    "/applications/{application_id}/skills",
    response_model=ApplicationSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map Skill to Application",
    description="Associate a catalog skill with an application, setting proficiency, years of experience, and primary priority.",
)
def add_application_skill(
    application_id: int,
    data: ApplicationSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationSkillResponse:
    service = SkillService(db)
    return service.add_application_skill(user_id=current_user.id, application_id=application_id, data=data)


@router.put(
    "/applications/{application_id}/skills/{skill_id}",
    response_model=ApplicationSkillResponse,
    summary="Update Application Skill Mapping",
    description="Update proficiency, years of experience, or primary flag for an application skill mapping.",
)
def update_application_skill(
    application_id: int,
    skill_id: int,
    data: ApplicationSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationSkillResponse:
    service = SkillService(db)
    return service.update_application_skill(
        user_id=current_user.id, application_id=application_id, skill_id=skill_id, data=data
    )


@router.delete(
    "/applications/{application_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Skill from Application",
    description="Unlink a skill from an application.",
)
def remove_application_skill(
    application_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = SkillService(db)
    service.remove_application_skill(user_id=current_user.id, application_id=application_id, skill_id=skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =====================================================================
# 3. Job Description ↔ Skill Mapping Endpoints
# =====================================================================

@router.get(
    "/job-descriptions/{job_description_id}/skills",
    response_model=List[JobDescriptionSkillResponse],
    summary="List Job Description Skills",
    description="Retrieve all skills linked to a specific job description.",
)
def list_job_description_skills(
    job_description_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[JobDescriptionSkillResponse]:
    service = SkillService(db)
    return service.list_job_description_skills(user_id=current_user.id, job_description_id=job_description_id)


@router.post(
    "/job-descriptions/{job_description_id}/skills",
    response_model=JobDescriptionSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map Skill to Job Description",
    description="Associate a catalog skill with a job description, specifying importance (REQUIRED/PREFERRED) and source section.",
)
def add_job_description_skill(
    job_description_id: int,
    data: JobDescriptionSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionSkillResponse:
    service = SkillService(db)
    return service.add_job_description_skill(
        user_id=current_user.id, job_description_id=job_description_id, data=data
    )


@router.put(
    "/job-descriptions/{job_description_id}/skills/{skill_id}",
    response_model=JobDescriptionSkillResponse,
    summary="Update Job Description Skill Mapping",
    description="Update importance (REQUIRED/PREFERRED) or source section for a job description skill mapping.",
)
def update_job_description_skill(
    job_description_id: int,
    skill_id: int,
    data: JobDescriptionSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionSkillResponse:
    service = SkillService(db)
    return service.update_job_description_skill(
        user_id=current_user.id, job_description_id=job_description_id, skill_id=skill_id, data=data
    )


@router.delete(
    "/job-descriptions/{job_description_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Skill from Job Description",
    description="Unlink a skill from a job description.",
)
def remove_job_description_skill(
    job_description_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = SkillService(db)
    service.remove_job_description_skill(
        user_id=current_user.id, job_description_id=job_description_id, skill_id=skill_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
