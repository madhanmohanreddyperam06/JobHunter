from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionListResponse,
    JobDescriptionResponse,
    JobDescriptionUpdate,
)
from app.services.job_description_service import JobDescriptionService

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


@router.get(
    "",
    response_model=JobDescriptionListResponse,
    summary="List Job Descriptions",
    description="Retrieve paginated job descriptions for the authenticated candidate with search, filter, and sorting.",
)
def list_job_descriptions(
    search: Optional[str] = Query(None, description="Search term for title, company, description, or sections"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (FULL_TIME, CONTRACT, etc.)"),
    work_arrangement: Optional[str] = Query(None, description="Filter by work arrangement (ONSITE, HYBRID, REMOTE)"),
    application_id: Optional[int] = Query(None, description="Filter by attached application ID"),
    sort_by: str = Query("captured_at", description="Sort field: captured_at, created_at, updated_at, title, company_name"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionListResponse:
    service = JobDescriptionService(db)
    items, total, total_pages = service.list_job_descriptions(
        user_id=current_user.id,
        search=search,
        employment_type=employment_type,
        work_arrangement=work_arrangement,
        application_id=application_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return JobDescriptionListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get(
    "/by-application/{application_id}",
    response_model=JobDescriptionResponse,
    summary="Get Job Description by Application ID",
    description="Retrieve job description linked to a specific application owned by candidate.",
)
def get_by_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    service = JobDescriptionService(db)
    jd = service.get_by_application_id(user_id=current_user.id, application_id=application_id)
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description for application {application_id} not found",
        )
    return jd


@router.get(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Get Job Description",
    description="Retrieve details and sections of a specific job description.",
)
def get_job_description(
    jd_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    service = JobDescriptionService(db)
    jd = service.get_job_description(user_id=current_user.id, jd_id=jd_id)
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )
    return jd


@router.post(
    "",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job Description",
    description="Create and link a structured job description to an application.",
)
def create_job_description(
    jd_in: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    service = JobDescriptionService(db)
    return service.create_job_description(user_id=current_user.id, jd_in=jd_in)


@router.put(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Update Job Description",
    description="Update an existing job description. Application link and captured_at are immutable.",
)
def update_job_description(
    jd_id: int,
    jd_in: JobDescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionResponse:
    service = JobDescriptionService(db)
    updated = service.update_job_description(
        user_id=current_user.id, jd_id=jd_id, jd_in=jd_in
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )
    return updated


@router.delete(
    "/{jd_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Job Description",
    description="Delete a job description. The associated application is preserved.",
)
def delete_job_description(
    jd_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = JobDescriptionService(db)
    deleted = service.delete_job_description(user_id=current_user.id, jd_id=jd_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
