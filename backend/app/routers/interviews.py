import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate,
    InterviewUpdate,
    InterviewStatusUpdate,
    InterviewResponse,
    InterviewListResponse,
)
from app.services import interview_service

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.get("", response_model=InterviewListResponse)
def list_interviews(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. SCHEDULED, COMPLETED)"),
    interview_type: Optional[str] = Query(None, description="Filter by type (e.g. VIDEO, PHONE, TECHNICAL)"),
    application_id: Optional[int] = Query(None, description="Filter by specific application ID"),
    search: Optional[str] = Query(None, description="Search term for round name, interviewer, notes, job title, company"),
    upcoming: Optional[bool] = Query(None, description="True for upcoming, False for past"),
    sort_by: str = Query("scheduled_at", description="Field to sort by: scheduled_at, created_at, round_name, status"),
    sort_order: str = Query("asc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a paginated list of interviews for the authenticated user.
    """
    items, total = interview_service.list_interviews(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        interview_type=interview_type,
        application_id=application_id,
        search=search,
        upcoming=upcoming,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return InterviewListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(
    data: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new interview round for an application owned by the authenticated user.
    """
    return interview_service.create_interview(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve an interview by its ID.
    """
    return interview_service.get_interview(
        db=db,
        user_id=current_user.id,
        interview_id=interview_id,
    )


@router.put("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: int,
    data: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update details of an existing interview.
    """
    return interview_service.update_interview(
        db=db,
        user_id=current_user.id,
        interview_id=interview_id,
        data=data,
    )


@router.patch("/{interview_id}/status", response_model=InterviewResponse)
def update_interview_status(
    interview_id: int,
    data: InterviewStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the status of an interview round.
    """
    return interview_service.update_interview_status(
        db=db,
        user_id=current_user.id,
        interview_id=interview_id,
        status_value=data.status,
    )


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an interview round.
    """
    interview_service.delete_interview(
        db=db,
        user_id=current_user.id,
        interview_id=interview_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
