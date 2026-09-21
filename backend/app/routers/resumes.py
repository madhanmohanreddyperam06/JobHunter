from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUpdate,
)
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.get(
    "",
    response_model=ResumeListResponse,
    summary="List Resumes",
    description="Retrieve paginated resumes for the authenticated candidate with search, filter, and sorting.",
)
def list_resumes(
    search: Optional[str] = Query(None, description="Search term for name or file name"),
    file_type: Optional[str] = Query(None, description="Filter by file type: pdf, docx"),
    sort_by: str = Query("created_at", description="Sort field: created_at, name, version"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeListResponse:
    service = ResumeService(db)
    items, total, total_pages = service.list_resumes(
        user_id=current_user.id,
        search=search,
        file_type=file_type,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return ResumeListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get Resume Metadata",
    description="Retrieve metadata for a specific resume owned by the authenticated candidate.",
)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    service = ResumeService(db)
    return service.get_resume(user_id=current_user.id, resume_id=resume_id)


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload New Resume",
    description="Upload a new candidate resume (PDF or DOCX, max 10MB). Automatically initiates version 1.",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume binary file (PDF or DOCX)"),
    name: str = Form(..., min_length=1, max_length=150, description="Display name for resume family"),
    description: Optional[str] = Form(None, description="Optional notes or targeted job profile"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    service = ResumeService(db)
    return await service.upload_resume(
        user_id=current_user.id,
        file=file,
        name=name,
        description=description,
    )


@router.post(
    "/{resume_id}/versions",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload New Resume Version",
    description="Upload an updated file version for an existing resume family. Increments version number.",
)
async def create_resume_version(
    resume_id: int,
    file: UploadFile = File(..., description="Updated resume binary file"),
    name: Optional[str] = Form(None, description="Optional override name for new version"),
    description: Optional[str] = Form(None, description="Optional notes for this version"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    service = ResumeService(db)
    return await service.create_version(
        user_id=current_user.id,
        resume_id=resume_id,
        file=file,
        name=name,
        description=description,
    )


@router.put(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Update Resume Metadata",
    description="Update editable metadata (name, description) for an existing resume.",
)
def update_resume(
    resume_id: int,
    resume_in: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    service = ResumeService(db)
    return service.update_resume(
        user_id=current_user.id,
        resume_id=resume_id,
        update_in=resume_in,
    )


@router.patch(
    "/{resume_id}/activate",
    response_model=ResumeResponse,
    summary="Designate Active Resume",
    description="Set target resume as the user's primary/active resume. Deactivates all other user resumes.",
)
def activate_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    service = ResumeService(db)
    return service.activate_resume(user_id=current_user.id, resume_id=resume_id)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Resume",
    description="Permanently delete a resume and its stored physical file. Rejected with 409 if referenced by applications.",
)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = ResumeService(db)
    service.delete_resume(user_id=current_user.id, resume_id=resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{resume_id}/download",
    summary="Download Resume File",
    description="Download the stored resume binary file (PDF/DOCX) using authenticated bearer token.",
)
def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    service = ResumeService(db)
    file_path, mime_type, filename = service.get_file_for_download(
        user_id=current_user.id, resume_id=resume_id
    )
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=filename,
    )


@router.get(
    "/{resume_id}/versions",
    response_model=List[ResumeResponse],
    summary="Get Resume Family Versions",
    description="Retrieve all versions in the resume's version family in descending version order.",
)
def get_resume_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ResumeResponse]:
    service = ResumeService(db)
    return service.get_versions(user_id=current_user.id, resume_id=resume_id)
