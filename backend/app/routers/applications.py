from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatusUpdate,
    ApplicationResponse,
    ApplicationListResponse,
)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List Applications",
    description="Retrieve paginated applications for the authenticated user with optional search, filtering, and sorting.",
)
def list_applications(
    search: Optional[str] = Query(None, description="Search term for company, job title, or location"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    sort_by: str = Query("applied_date", description="Sort field: applied_date, created_at, job_title, status, company"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    service = ApplicationService(db)
    items, total, total_pages = service.list_applications(
        user_id=current_user.id,
        search=search,
        status=status,
        location=location,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return ApplicationListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Application",
    description="Create a new job application owned by the authenticated user. Auto-resolves company name.",
)
def create_application(
    app_in: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    service = ApplicationService(db)
    created = service.create_application(user_id=current_user.id, app_in=app_in)
    return created


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get Application Detail",
    description="Retrieve details of a single application owned by the authenticated user. Returns 404 if not found.",
)
def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    service = ApplicationService(db)
    app = service.get_application(user_id=current_user.id, application_id=application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return app


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Update Application",
    description="Update an application owned by the authenticated user. Returns 404 if not found or unauthorized.",
)
def update_application(
    application_id: int,
    app_in: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    service = ApplicationService(db)
    updated = service.update_application(
        user_id=current_user.id, application_id=application_id, app_in=app_in
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return updated


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update Application Status",
    description="Update only the status of an application owned by the authenticated user.",
)
def update_application_status(
    application_id: int,
    status_in: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    service = ApplicationService(db)
    updated = service.update_application_status(
        user_id=current_user.id, application_id=application_id, status=status_in.status
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return updated


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Application",
    description="Permanently delete an application owned by the authenticated user.",
)
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = ApplicationService(db)
    success = service.delete_application(user_id=current_user.id, application_id=application_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
