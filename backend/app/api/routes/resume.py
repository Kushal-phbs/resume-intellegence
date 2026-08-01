"""Resume management API endpoints."""

from __future__ import annotations

from pathlib import Path as FilePath
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.config import settings
from app.core.exceptions import ValidationException
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import limit
from app.dependencies.resume import get_resume_service
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse, ResumeUploadResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Resume",
    description="Upload a new resume file and create its initial stored version.",
    responses={
        201: {"description": "Resume uploaded successfully."},
        400: {"description": "Invalid upload input."},
        401: {"description": "Authentication required."},
        413: {"description": "Uploaded file is too large."},
        415: {"description": "Unsupported file type."},
        429: {"description": "Upload rate limit exceeded."},
    },
)
async def upload_resume_endpoint(
    title: str = Form(
        min_length=1,
        max_length=255,
        description="Resume title shown in resume listings.",
    ),
    file: UploadFile = File(..., description="Resume file to upload."),
    _: None = Depends(
        limit(
            bucket="resume_upload",
            requests=settings.rate_limit_resume_upload_requests,
        )
    ),
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


@router.get(
    "",
    response_model=ResumeListResponse,
    summary="List Resumes",
    description="List resumes owned by the authenticated user.",
    responses={
        200: {"description": "Resume list returned."},
        401: {"description": "Authentication required."},
    },
)
async def list_resumes_endpoint(
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeListResponse:
    """List resumes owned by the authenticated user."""
    return await resume_service.list_user_resumes(current_user.id)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get Resume",
    description="Retrieve one resume owned by the authenticated user.",
    responses={
        200: {"description": "Resume returned."},
        401: {"description": "Authentication required."},
        404: {"description": "Resume not found."},
    },
)
async def get_resume_endpoint(
    resume_id: UUID = Path(description="Resume identifier."),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    """Return a single resume owned by the authenticated user."""
    return await resume_service.get_resume(user_id=current_user.id, resume_id=resume_id)


@router.get(
    "/{resume_id}/download",
    summary="Download Resume File",
    description="Download the latest stored file version for a resume.",
    responses={
        200: {"description": "Resume file download response."},
        401: {"description": "Authentication required."},
        404: {"description": "Resume or file not found."},
    },
)
async def download_resume_endpoint(
    resume_id: UUID = Path(description="Resume identifier."),
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
        filename=FilePath(download_path).name,
    )


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Resume",
    description="Delete a resume and its stored versions for the current user.",
    responses={
        204: {"description": "Resume deleted."},
        401: {"description": "Authentication required."},
        404: {"description": "Resume not found."},
    },
)
async def delete_resume_endpoint(
    resume_id: UUID = Path(description="Resume identifier."),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> Response:
    """Delete a resume owned by the authenticated user."""
    await resume_service.delete_resume(user_id=current_user.id, resume_id=resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
