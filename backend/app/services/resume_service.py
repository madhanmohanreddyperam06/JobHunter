"""
ResumeService layer.
Encapsulates database operations, version hierarchy tracking, file upload validation,
filesystem storage persistence, download handling, and application association guards.
"""
import logging
import math
import os
import uuid
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import asc, cast, desc, func, or_, select, Integer
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.application import Application
from app.models.resume import Resume
from app.schemas.resume import ResumeUpdate

logger = logging.getLogger("uvicorn.error")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB maximum allowed upload size

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/x-pdf",
    "application/octet-stream",  # Windows browsers sometimes send octet-stream for docx
}


class ResumeService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Validates uploaded file existence, file extension, and MIME type.
        Returns: (sanitized_original_filename, file_extension)
        """
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File is required and must have a valid name.",
            )

        original_filename = os.path.basename(file.filename.strip())
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type '{ext}'. Only PDF and DOCX files are allowed.",
            )

        if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported MIME type '{file.content_type}'. Only PDF and DOCX documents are allowed.",
            )

        return original_filename, ext

    def list_resumes(
        self,
        user_id: int,
        search: Optional[str] = None,
        file_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Resume], int, int]:
        """
        Retrieve paginated list of resumes for the user with search and sorting.
        Returns: (items, total_count, total_pages)
        """
        query = (
            select(Resume)
            .options(joinedload(Resume.applications))
            .where(Resume.user_id == user_id)
        )
        count_query = select(func.count(Resume.id)).where(Resume.user_id == user_id)

        # Search filter by resume name or original filename
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            search_clause = or_(
                func.lower(Resume.name).like(term),
                func.lower(Resume.file_name).like(term),
            )
            query = query.where(search_clause)
            count_query = count_query.where(search_clause)

        # File type filter
        if file_type and file_type.strip():
            ft = file_type.strip().lower()
            if ft == "pdf":
                query = query.where(func.lower(Resume.file_name).like("%.pdf"))
                count_query = count_query.where(func.lower(Resume.file_name).like("%.pdf"))
            elif ft == "docx":
                query = query.where(func.lower(Resume.file_name).like("%.docx"))
                count_query = count_query.where(func.lower(Resume.file_name).like("%.docx"))

        total = self.db.execute(count_query).scalar() or 0

        # Whitelist sorting fields
        sort_col = Resume.created_at
        if sort_by:
            sb = sort_by.strip().lower()
            if sb == "name":
                sort_col = Resume.name
            elif sb == "version":
                sort_col = cast(Resume.version, Integer)
            elif sb == "created_at":
                sort_col = Resume.created_at

        direction = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(direction(sort_col), desc(Resume.id))

        offset = (page - 1) * page_size
        items = self.db.execute(query.offset(offset).limit(page_size)).unique().scalars().all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return items, total, total_pages

    def get_resume(self, user_id: int, resume_id: int) -> Resume:
        """
        Retrieve a single resume owned by user_id.
        Raises HTTP 404 if not found or owned by another user.
        """
        stmt = (
            select(Resume)
            .options(joinedload(Resume.applications))
            .where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = self.db.execute(stmt).unique().scalars().first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )
        return resume

    async def upload_resume(
        self,
        user_id: int,
        file: UploadFile,
        name: str,
        description: Optional[str] = None,
    ) -> Resume:
        """
        Uploads and stores a new resume family (version 1).
        Enforces 10 MB size limit, safe filesystem storage, and ownership isolation.
        """
        original_filename, ext = self._validate_file(file)

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large. Maximum size is 10 MB.",
            )

        # Check if user has any active resume; if none, auto-activate this first resume
        active_count = (
            self.db.execute(
                select(func.count(Resume.id)).where(
                    Resume.user_id == user_id, Resume.is_active.is_(True)
                )
            ).scalar()
            or 0
        )
        is_active = active_count == 0

        mime_type = file.content_type or ("application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        new_resume = Resume(
            user_id=user_id,
            parent_id=None,
            name=name.strip(),
            version="1",
            file_name=original_filename,
            file_size=file_size,
            mime_type=mime_type,
            is_active=is_active,
            description=description.strip() if description else None,
        )
        self.db.add(new_resume)
        self.db.commit()
        self.db.refresh(new_resume)

        # Save file safely on filesystem
        safe_filename = f"resume_{new_resume.id}_{uuid.uuid4().hex[:8]}{ext}"
        target_dir = os.path.join(settings.resumes_storage_path, str(user_id), str(new_resume.id))
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, safe_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        new_resume.file_path = file_path
        self.db.commit()
        self.db.refresh(new_resume)

        return self.get_resume(user_id, new_resume.id)

    async def create_version(
        self,
        user_id: int,
        resume_id: int,
        file: UploadFile,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Resume:
        """
        Creates a new version for an existing resume family.
        Next version is backend-calculated as max(family versions) + 1.
        Preserves all historical versions.
        """
        existing = self.get_resume(user_id, resume_id)
        original_filename, ext = self._validate_file(file)

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large. Maximum size is 10 MB.",
            )

        # Identify family root
        root_id = existing.parent_id if existing.parent_id is not None else existing.id
        root_resume = self.get_resume(user_id, root_id)

        # Calculate next version
        family_stmt = select(Resume).where(
            Resume.user_id == user_id,
            or_(Resume.id == root_id, Resume.parent_id == root_id),
        )
        family_members = self.db.execute(family_stmt).scalars().all()

        existing_versions = []
        for mem in family_members:
            try:
                existing_versions.append(int(mem.version))
            except (ValueError, TypeError):
                pass

        next_ver = str(max(existing_versions, default=0) + 1)
        version_name = name.strip() if name and name.strip() else root_resume.name
        mime_type = file.content_type or ("application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        new_version = Resume(
            user_id=user_id,
            parent_id=root_id,
            name=version_name,
            version=next_ver,
            file_name=original_filename,
            file_size=file_size,
            mime_type=mime_type,
            is_active=False,
            description=description.strip() if description else existing.description,
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)

        # Save file to filesystem
        safe_filename = f"resume_{new_version.id}_{uuid.uuid4().hex[:8]}{ext}"
        target_dir = os.path.join(settings.resumes_storage_path, str(user_id), str(new_version.id))
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, safe_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        new_version.file_path = file_path
        self.db.commit()
        self.db.refresh(new_version)

        return self.get_resume(user_id, new_version.id)

    def update_resume(
        self, user_id: int, resume_id: int, update_in: ResumeUpdate
    ) -> Resume:
        """
        Updates editable metadata (name, description) for a resume.
        Protects version, file_path, file_size, user_id, and created_at.
        """
        resume = self.get_resume(user_id, resume_id)
        update_data = update_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"]:
            resume.name = update_data["name"].strip()
        if "description" in update_data:
            resume.description = update_data["description"].strip() if update_data["description"] else None

        self.db.commit()
        self.db.refresh(resume)
        return self.get_resume(user_id, resume.id)

    def activate_resume(self, user_id: int, resume_id: int) -> Resume:
        """
        Designates the target resume as the user's single active resume.
        Deactivates all other user resumes in a single atomic transaction.
        """
        resume = self.get_resume(user_id, resume_id)

        # Deactivate all user's resumes
        all_user_resumes = (
            self.db.execute(select(Resume).where(Resume.user_id == user_id))
            .scalars()
            .all()
        )
        for r in all_user_resumes:
            r.is_active = False

        resume.is_active = True
        self.db.commit()
        self.db.refresh(resume)
        return self.get_resume(user_id, resume.id)

    def delete_resume(self, user_id: int, resume_id: int) -> None:
        """
        Deletes a resume and its stored physical file.
        Rejects deletion with HTTP 409 Conflict if any application references this resume.
        """
        resume = self.get_resume(user_id, resume_id)

        # Verify application references
        app_count = (
            self.db.execute(
                select(func.count(Application.id)).where(Application.resume_id == resume_id)
            ).scalar()
            or 0
        )

        if app_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This resume is currently associated with one or more applications and cannot be deleted.",
            )

        # Remove physical file from filesystem
        if resume.file_path and os.path.exists(resume.file_path):
            try:
                os.remove(resume.file_path)
                folder = os.path.dirname(resume.file_path)
                if os.path.exists(folder) and not os.listdir(folder):
                    os.rmdir(folder)
            except OSError as exc:
                logger.warning("Could not delete stored resume file: %s", exc)

        self.db.delete(resume)
        self.db.commit()

    def get_versions(self, user_id: int, resume_id: int) -> List[Resume]:
        """
        Retrieve all versions belonging to the resume's family in descending version order.
        """
        existing = self.get_resume(user_id, resume_id)
        root_id = existing.parent_id if existing.parent_id is not None else existing.id

        stmt = (
            select(Resume)
            .options(joinedload(Resume.applications))
            .where(
                Resume.user_id == user_id,
                or_(Resume.id == root_id, Resume.parent_id == root_id),
            )
            .order_by(desc(cast(Resume.version, Integer)), desc(Resume.created_at))
        )
        return self.db.execute(stmt).unique().scalars().all()

    def get_file_for_download(self, user_id: int, resume_id: int) -> Tuple[str, str, str]:
        """
        Validates ownership and returns (file_path, mime_type, download_filename).
        Raises 404 if resume or physical file does not exist.
        """
        resume = self.get_resume(user_id, resume_id)

        if not resume.file_path or not os.path.exists(resume.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file not found on disk.",
            )

        download_filename = resume.file_name or f"{resume.name}.pdf"
        return resume.file_path, resume.mime_type, download_filename
