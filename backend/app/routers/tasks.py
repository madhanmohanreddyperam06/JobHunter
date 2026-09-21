import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskResponse,
    TaskListResponse,
    TaskSummaryResponse,
)
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. TODO, IN_PROGRESS, COMPLETED, CANCELLED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (e.g. LOW, MEDIUM, HIGH, URGENT)"),
    application_id: Optional[int] = Query(None, description="Filter by associated job application ID"),
    search: Optional[str] = Query(None, description="Search term across title, description, job title, company"),
    due: Optional[str] = Query(None, description="Filter due timeframe: overdue, today, upcoming"),
    sort_by: Optional[str] = Query(None, description="Sort field: due_date, priority, created_at, title, status"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve paginated tasks for the authenticated user with search and filtering.
    """
    items, total = task_service.list_tasks(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        application_id=application_id,
        search=search,
        due=due,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=TaskSummaryResponse)
def get_task_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve operational KPI summary counts for the user's tasks.
    """
    summary = task_service.get_task_summary(db=db, user_id=current_user.id)
    return TaskSummaryResponse(**summary)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new task action item for the authenticated user.
    """
    return task_service.create_task(
        db=db,
        user_id=current_user.id,
        data=data,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single task by ID.
    """
    return task_service.get_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
    )


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update editable fields of an existing task.
    """
    return task_service.update_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
        data=data,
    )


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update task status with automatic completed_at management.
    """
    return task_service.update_task_status(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
        status_value=data.status,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a task.
    """
    task_service.delete_task(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
