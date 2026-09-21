import math
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select, func, distinct, or_, desc, asc, case
from sqlalchemy.orm import Session, joinedload

from app.models.task import Task
from app.models.application import Application
from app.models.company import Company
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    VALID_TASK_PRIORITIES,
    VALID_TASK_STATUSES,
)


class TaskService:
    """
    Business service layer for job search tasks, follow-ups, and action items.
    Enforces user isolation, application association verification, and completed_at lifecycle.
    """
    def __init__(self, db: Session):
        self.db = db

    def list_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        application_id: Optional[int] = None,
        search: Optional[str] = None,
        due: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[Task], int]:
        return list_tasks(
            db=self.db,
            user_id=user_id,
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

    def get_task(self, user_id: int, task_id: int) -> Task:
        return get_task(self.db, user_id, task_id)

    def create_task(self, user_id: int, data: TaskCreate) -> Task:
        return create_task(self.db, user_id, data)

    def update_task(self, user_id: int, task_id: int, data: TaskUpdate) -> Task:
        return update_task(self.db, user_id, task_id, data)

    def update_task_status(self, user_id: int, task_id: int, status_value: str) -> Task:
        return update_task_status(self.db, user_id, task_id, status_value)

    def delete_task(self, user_id: int, task_id: int) -> bool:
        return delete_task(self.db, user_id, task_id)

    def get_task_summary(self, user_id: int) -> Dict[str, int]:
        return get_task_summary(self.db, user_id)


def list_tasks(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    application_id: Optional[int] = None,
    search: Optional[str] = None,
    due: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> Tuple[List[Task], int]:
    """
    List tasks owned by the authenticated user with search, filtering, and sorting.
    """
    query = (
        select(Task)
        .outerjoin(Application, Task.application_id == Application.id)
        .outerjoin(Company, Application.company_id == Company.id)
        .where(Task.user_id == user_id)
        .options(
            joinedload(Task.application).joinedload(Application.company)
        )
    )

    count_query = (
        select(func.count(distinct(Task.id)))
        .select_from(Task)
        .outerjoin(Application, Task.application_id == Application.id)
        .outerjoin(Company, Application.company_id == Company.id)
        .where(Task.user_id == user_id)
    )

    # Filter by status
    if status:
        normalized_status = status.strip().upper()
        query = query.where(Task.status == normalized_status)
        count_query = count_query.where(Task.status == normalized_status)

    # Filter by priority
    if priority:
        normalized_priority = priority.strip().upper()
        query = query.where(Task.priority == normalized_priority)
        count_query = count_query.where(Task.priority == normalized_priority)

    # Filter by application
    if application_id is not None:
        query = query.where(Task.application_id == application_id)
        count_query = count_query.where(Task.application_id == application_id)

    # Filter by due timeframe
    if due:
        due_normalized = due.strip().lower()
        now = datetime.utcnow()
        if due_normalized == "overdue":
            overdue_cond = (
                (Task.due_date < now) &
                (Task.status.notin_(["COMPLETED", "CANCELLED"]))
            )
            query = query.where(overdue_cond)
            count_query = count_query.where(overdue_cond)
        elif due_normalized == "today":
            today_cond = (
                (func.date(Task.due_date) == func.date(now)) &
                (Task.status.notin_(["COMPLETED", "CANCELLED"]))
            )
            query = query.where(today_cond)
            count_query = count_query.where(today_cond)
        elif due_normalized == "upcoming":
            upcoming_cond = (
                (Task.due_date >= now) &
                (Task.status.notin_(["COMPLETED", "CANCELLED"]))
            )
            query = query.where(upcoming_cond)
            count_query = count_query.where(upcoming_cond)

    # Search filter across title, description, job title, company name
    if search:
        term = f"%{search.strip()}%"
        search_filter = or_(
            Task.title.ilike(term),
            Task.description.ilike(term),
            Application.job_title.ilike(term),
            Company.name.ilike(term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = db.scalar(count_query) or 0

    # Whitelist sorting fields
    sort_column_map = {
        "due_date": Task.due_date,
        "priority": Task.priority,
        "created_at": Task.created_at,
        "title": Task.title,
        "status": Task.status,
    }

    is_desc = (sort_order.lower().strip() == "desc") if sort_order else False

    if sort_by and sort_by.lower().strip() in sort_column_map:
        sort_col = sort_column_map[sort_by.lower().strip()]
        if is_desc:
            query = query.order_by(desc(sort_col), desc(Task.id))
        else:
            query = query.order_by(asc(sort_col), asc(Task.id))
    else:
        # Default: incomplete tasks first, then due_date ascending (nulls last in MySQL), then id desc
        incomplete_first = case((Task.status.in_(["COMPLETED", "CANCELLED"]), 1), else_=0)
        query = query.order_by(
            asc(incomplete_first),
            Task.due_date.is_(None),
            asc(Task.due_date),
            desc(Task.id),
        )

    # Pagination
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    results = db.scalars(query).unique().all()
    return list(results), total


def get_task(db: Session, user_id: int, task_id: int) -> Task:
    """
    Retrieve single task by ID, enforcing user ownership.
    Raises 404 if not found or unowned.
    """
    stmt = (
        select(Task)
        .where(Task.id == task_id, Task.user_id == user_id)
        .options(
            joinedload(Task.application).joinedload(Application.company)
        )
    )
    task = db.scalar(stmt)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task #{task_id} not found"
        )
    return task


def create_task(db: Session, user_id: int, data: TaskCreate) -> Task:
    """
    Create a new task. If application_id is provided, verifies that it belongs to current_user.
    """
    if data.application_id is not None:
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

    normalized_status = (data.status or "TODO").strip().upper()
    initial_completed_at = datetime.utcnow() if normalized_status == "COMPLETED" else None

    task = Task(
        user_id=user_id,
        application_id=data.application_id,
        title=data.title.strip(),
        description=data.description.strip() if data.description else None,
        priority=(data.priority or "MEDIUM").strip().upper(),
        due_date=data.due_date,
        completed_at=initial_completed_at,
        status=normalized_status,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return get_task(db, user_id, task.id)


def update_task(db: Session, user_id: int, task_id: int, data: TaskUpdate) -> Task:
    """
    Update editable fields of an existing task owned by user_id.
    Manages completed_at lifecycle when status changes.
    """
    task = get_task(db, user_id, task_id)

    # Application ownership verification if application_id changed
    if data.application_id is not None and data.application_id != task.application_id:
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
        task.application_id = data.application_id
    elif data.application_id is None and "application_id" in data.model_fields_set:
        task.application_id = None

    # Status & completed_at lifecycle
    if data.status is not None:
        normalized_status = data.status.strip().upper()
        if normalized_status == "COMPLETED" and task.status != "COMPLETED":
            task.completed_at = datetime.utcnow()
        elif task.status == "COMPLETED" and normalized_status in ("TODO", "IN_PROGRESS", "CANCELLED"):
            task.completed_at = None
        task.status = normalized_status

    if data.title is not None:
        task.title = data.title.strip()
    if data.description is not None:
        task.description = data.description.strip() if data.description else None
    if data.priority is not None:
        task.priority = data.priority.strip().upper()
    if data.due_date is not None or "due_date" in data.model_fields_set:
        task.due_date = data.due_date

    db.commit()
    db.refresh(task)
    return get_task(db, user_id, task.id)


def update_task_status(db: Session, user_id: int, task_id: int, status_value: str) -> Task:
    """
    Update only task status with automatic completed_at management.
    """
    normalized_status = status_value.strip().upper()
    if normalized_status not in VALID_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_value}'. Allowed: {', '.join(sorted(VALID_TASK_STATUSES))}"
        )

    task = get_task(db, user_id, task_id)

    if normalized_status == "COMPLETED" and task.status != "COMPLETED":
        task.completed_at = datetime.utcnow()
    elif task.status == "COMPLETED" and normalized_status in ("TODO", "IN_PROGRESS", "CANCELLED"):
        task.completed_at = None

    task.status = normalized_status

    db.commit()
    db.refresh(task)
    return get_task(db, user_id, task.id)


def delete_task(db: Session, user_id: int, task_id: int) -> bool:
    """
    Delete a task owned by user_id.
    """
    task = get_task(db, user_id, task_id)
    db.delete(task)
    db.commit()
    return True


def get_task_summary(db: Session, user_id: int) -> Dict[str, int]:
    """
    Compute real KPI counts for tasks owned by user_id.
    """
    now = datetime.utcnow()

    total = db.scalar(select(func.count(Task.id)).where(Task.user_id == user_id)) or 0
    pending = db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.status.in_(["TODO", "IN_PROGRESS"])
        )
    ) or 0
    completed = db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.status == "COMPLETED"
        )
    ) or 0
    overdue = db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.due_date < now,
            Task.status.notin_(["COMPLETED", "CANCELLED"])
        )
    ) or 0
    due_today = db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == user_id,
            func.date(Task.due_date) == func.date(now),
            Task.status.notin_(["COMPLETED", "CANCELLED"])
        )
    ) or 0

    return {
        "total": total,
        "pending": pending,
        "due_today": due_today,
        "overdue": overdue,
        "completed": completed,
    }
