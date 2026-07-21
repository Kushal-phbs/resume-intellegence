"""Resume management API endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.core.exceptions import ValidationException
from app.dependencies.auth import get_current_user
from app.dependencies.resume import get_resume_service
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse, ResumeUploadResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume_endpoint(
    title: str = Form(min_length=1, max_length=255),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeUploadResponse:
    """Upload a new resume for the authenticated user."""
    if not file.filename:
        raise ValidationException("Uploaded file must have a filename")

    content = await file.read()
    return await resume_service.upload_resume(
        user_id=current_user.id,
        title=title,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )


@router.get("", response_model=ResumeListResponse)
async def list_resumes_endpoint(
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeListResponse:
    """List resumes owned by the authenticated user."""
    return await resume_service.list_user_resumes(current_user.id)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    """Return a single resume owned by the authenticated user."""
    return await resume_service.get_resume(user_id=current_user.id, resume_id=resume_id)


@router.get("/{resume_id}/download")
async def download_resume_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> FileResponse:
    """Download the stored file for a resume owned by the authenticated user."""
    download_path = await resume_service.get_download_path(
        user_id=current_user.id,
        resume_id=resume_id,
    )
    return FileResponse(
        path=download_path,
        filename=Path(download_path).name,
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> Response:
    """Delete a resume owned by the authenticated user."""
    await resume_service.delete_resume(user_id=current_user.id, resume_id=resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
