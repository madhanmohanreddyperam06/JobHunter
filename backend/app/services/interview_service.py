import math
from datetime import datetime
from typing import Optional, Tuple, List
from fastapi import HTTPException, status
from sqlalchemy import select, func, distinct, or_, desc, asc
from sqlalchemy.orm import Session, joinedload

from app.models.interview import Interview
from app.models.application import Application
from app.models.company import Company
from app.schemas.interview import InterviewCreate, InterviewUpdate, VALID_INTERVIEW_STATUSES


class InterviewService:
    """
    Business service layer for interview scheduling and tracking.
    Enforces that all operations are isolated to the authenticated user via application ownership.
    """
    def __init__(self, db: Session):
        self.db = db

    def list_interviews(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        interview_type: Optional[str] = None,
        application_id: Optional[int] = None,
        search: Optional[str] = None,
        upcoming: Optional[bool] = None,
        sort_by: str = "scheduled_at",
        sort_order: str = "asc",
    ) -> Tuple[List[Interview], int]:
        return list_interviews(
            db=self.db,
            user_id=user_id,
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

    def get_interview(self, user_id: int, interview_id: int) -> Interview:
        return get_interview(self.db, user_id, interview_id)

    def create_interview(self, user_id: int, data: InterviewCreate) -> Interview:
        return create_interview(self.db, user_id, data)

    def update_interview(self, user_id: int, interview_id: int, data: InterviewUpdate) -> Interview:
        return update_interview(self.db, user_id, interview_id, data)

    def update_interview_status(self, user_id: int, interview_id: int, status_value: str) -> Interview:
        return update_interview_status(self.db, user_id, interview_id, status_value)

    def delete_interview(self, user_id: int, interview_id: int) -> bool:
        return delete_interview(self.db, user_id, interview_id)


def list_interviews(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    interview_type: Optional[str] = None,
    application_id: Optional[int] = None,
    search: Optional[str] = None,
    upcoming: Optional[bool] = None,
    sort_by: str = "scheduled_at",
    sort_order: str = "asc",
) -> Tuple[List[Interview], int]:
    """
    List interviews belonging to applications owned by the given user_id.
    Includes eager-loading of parent application and company details.
    """
    query = (
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .outerjoin(Company, Application.company_id == Company.id)
        .where(Application.user_id == user_id)
        .options(
            joinedload(Interview.application).joinedload(Application.company)
        )
    )

    count_query = (
        select(func.count(distinct(Interview.id)))
        .select_from(Interview)
        .join(Application, Interview.application_id == Application.id)
        .outerjoin(Company, Application.company_id == Company.id)
        .where(Application.user_id == user_id)
    )

    # Filter by status
    if status:
        normalized_status = status.strip().upper()
        query = query.where(Interview.status == normalized_status)
        count_query = count_query.where(Interview.status == normalized_status)

    # Filter by interview type
    if interview_type:
        normalized_type = interview_type.strip().upper()
        query = query.where(func.upper(Interview.interview_type) == normalized_type)
        count_query = count_query.where(func.upper(Interview.interview_type) == normalized_type)

    # Filter by application
    if application_id is not None:
        query = query.where(Interview.application_id == application_id)
        count_query = count_query.where(Interview.application_id == application_id)

    # Upcoming vs Past filter
    if upcoming is True:
        now = datetime.utcnow()
        upcoming_condition = or_(
            Interview.scheduled_at >= now,
            Interview.status == "SCHEDULED"
        )
        query = query.where(upcoming_condition)
        count_query = count_query.where(upcoming_condition)
    elif upcoming is False:
        now = datetime.utcnow()
        past_condition = or_(
            Interview.scheduled_at < now,
            Interview.status.in_(["COMPLETED", "CANCELLED", "NO_SHOW"])
        )
        query = query.where(past_condition)
        count_query = count_query.where(past_condition)

    # Search filter across round_name, interviewer, notes, job_title, company name
    if search:
        search_pattern = f"%{search.strip()}%"
        search_filter = or_(
            Interview.round_name.ilike(search_pattern),
            Interview.interviewer.ilike(search_pattern),
            Interview.notes.ilike(search_pattern),
            Application.job_title.ilike(search_pattern),
            Company.name.ilike(search_pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Total record count
    total = db.scalar(count_query) or 0

    # Sorting
    sort_column_map = {
        "scheduled_at": Interview.scheduled_at,
        "created_at": Interview.created_at,
        "round_name": Interview.round_name,
        "status": Interview.status,
    }
    sort_col = sort_column_map.get(sort_by, Interview.scheduled_at)

    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_col), desc(Interview.id))
    else:
        query = query.order_by(asc(sort_col), asc(Interview.id))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    results = db.scalars(query).unique().all()
    return list(results), total


def get_interview(db: Session, user_id: int, interview_id: int) -> Interview:
    """
    Retrieve a single interview by ID, ensuring it belongs to an application owned by the user.
    Raises 404 if not found or unauthorized.
    """
    stmt = (
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .where(Interview.id == interview_id, Application.user_id == user_id)
        .options(
            joinedload(Interview.application).joinedload(Application.company)
        )
    )
    interview = db.scalar(stmt)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview #{interview_id} not found"
        )
    return interview


def create_interview(db: Session, user_id: int, data: InterviewCreate) -> Interview:
    """
    Create a new interview for a job application owned by the user.
    Raises 404 if the application does not exist or is not owned by the user.
    """
    # Verify application ownership
    app_stmt = select(Application).where(
        Application.id == data.application_id,
        Application.user_id == user_id
    )
    app = db.scalar(app_stmt)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{data.application_id} not found or access denied"
        )

    # Insert interview
    interview = Interview(
        application_id=data.application_id,
        round_name=data.round_name,
        interview_type=data.interview_type or "VIDEO",
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes or 45,
        location=data.location,
        meeting_link=data.meeting_link,
        interviewer=data.interviewer,
        interviewer_email=data.interviewer_email,
        status=data.status or "SCHEDULED",
        notes=data.notes,
    )

    db.add(interview)
    db.commit()
    db.refresh(interview)

    return get_interview(db, user_id, interview.id)


def update_interview(db: Session, user_id: int, interview_id: int, data: InterviewUpdate) -> Interview:
    """
    Update details of an existing interview owned by the user.
    """
    interview = get_interview(db, user_id, interview_id)

    # If re-assigning application_id, verify new application ownership
    if data.application_id is not None and data.application_id != interview.application_id:
        app_stmt = select(Application).where(
            Application.id == data.application_id,
            Application.user_id == user_id
        )
        new_app = db.scalar(app_stmt)
        if not new_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target Application #{data.application_id} not found or access denied"
            )
        interview.application_id = data.application_id

    # Update individual fields
    updatable_fields = [
        "round_name",
        "interview_type",
        "scheduled_at",
        "duration_minutes",
        "location",
        "meeting_link",
        "interviewer",
        "interviewer_email",
        "status",
        "notes",
    ]

    for field in updatable_fields:
        val = getattr(data, field)
        if val is not None:
            setattr(interview, field, val)

    db.commit()
    db.refresh(interview)
    return get_interview(db, user_id, interview.id)


def update_interview_status(db: Session, user_id: int, interview_id: int, status_value: str) -> Interview:
    """
    Update the status of an interview with enum validation.
    """
    normalized_status = status_value.strip().upper()
    if normalized_status not in VALID_INTERVIEW_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_value}'. Allowed: {', '.join(sorted(VALID_INTERVIEW_STATUSES))}"
        )

    interview = get_interview(db, user_id, interview_id)
    interview.status = normalized_status

    db.commit()
    db.refresh(interview)
    return get_interview(db, user_id, interview.id)


def delete_interview(db: Session, user_id: int, interview_id: int) -> bool:
    """
    Delete an interview owned by the user.
    """
    interview = get_interview(db, user_id, interview_id)
    db.delete(interview)
    db.commit()
    return True
