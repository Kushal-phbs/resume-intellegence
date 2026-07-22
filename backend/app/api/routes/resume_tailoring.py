"""Resume tailoring API endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import FileResponse

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import limit
from app.dependencies.resume_tailoring import (
    get_export_service,
    get_resume_tailoring_service,
)
from app.models.user import User
from app.schemas.resume_tailoring import (
    CoverLetterResponse,
    ResumeVersionResponse,
    TailoringSessionResponse,
    TailoringSummaryResponse,
)
from app.services.export_service import ExportService
from app.services.resume_tailoring_service import ResumeTailoringService

router = APIRouter(prefix="/resume-tailoring", tags=["Resume Tailoring"])
export_router = APIRouter(prefix="/export", tags=["Export"])

_TAILORING_RESPONSES = {
    401: {"description": "Authentication required"},
    404: {"description": "Resume, job description, or tailoring session not found"},
    502: {"description": "Tailoring failed"},
}

_EXPORT_RESPONSES = {
    401: {"description": "Authentication required"},
    404: {"description": "Export source not found"},
    400: {"description": "Unsupported export format"},
}


@router.post(
    "/{resume_id}/{job_id}",
    response_model=TailoringSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Tailored Resume",
    description=(
        "Generate a tailored resume version and cover letter for the provided "
        "resume and job description."
    ),
    responses=_TAILORING_RESPONSES,
)
async def create_tailoring_session_endpoint(
    resume_id: UUID,
    job_id: UUID,
    _: None = Depends(
        limit(
            bucket="resume_tailoring",
            requests=settings.rate_limit_resume_tailoring_requests,
        )
    ),
    current_user: User = Depends(get_current_user),
    tailoring_service: ResumeTailoringService = Depends(get_resume_tailoring_service),
) -> TailoringSummaryResponse:
    result = await tailoring_service.tailor_resume(
        user_id=current_user.id,
        resume_id=resume_id,
        job_description_id=job_id,
    )
    return TailoringSummaryResponse(
        session=TailoringSessionResponse.model_validate(result.session),
        resume_version=ResumeVersionResponse.model_validate(result.resume_version),
        cover_letter=CoverLetterResponse.model_validate(result.cover_letter),
    )


@router.get(
    "/history",
    response_model=list[TailoringSessionResponse],
    summary="List Tailoring History",
    description="List tailoring sessions for the authenticated user.",
    responses=_TAILORING_RESPONSES,
)
async def list_tailoring_history_endpoint(
    current_user: User = Depends(get_current_user),
    tailoring_service: ResumeTailoringService = Depends(get_resume_tailoring_service),
) -> list[TailoringSessionResponse]:
    items = await tailoring_service.list_history(user_id=current_user.id)
    return [TailoringSessionResponse.model_validate(item) for item in items]


@router.get(
    "/{session_id}",
    response_model=TailoringSessionResponse,
    summary="Get Tailoring Session",
    description="Return tailoring session details by session id.",
    responses=_TAILORING_RESPONSES,
)
async def get_tailoring_session_endpoint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    tailoring_service: ResumeTailoringService = Depends(get_resume_tailoring_service),
) -> TailoringSessionResponse:
    result = await tailoring_service.get_session(
        user_id=current_user.id,
        session_id=session_id,
    )
    return TailoringSessionResponse.model_validate(result)


@router.get(
    "/{session_id}/resume",
    response_model=ResumeVersionResponse,
    summary="Get Tailored Resume Version",
    description="Return generated tailored resume version for a session.",
    responses=_TAILORING_RESPONSES,
)
async def get_tailored_resume_endpoint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    tailoring_service: ResumeTailoringService = Depends(get_resume_tailoring_service),
) -> ResumeVersionResponse:
    result = await tailoring_service.get_resume_version(
        user_id=current_user.id,
        session_id=session_id,
    )
    return ResumeVersionResponse.model_validate(result)


@router.get(
    "/{session_id}/cover-letter",
    response_model=CoverLetterResponse,
    summary="Get Generated Cover Letter",
    description="Return generated cover letter for a session.",
    responses=_TAILORING_RESPONSES,
)
async def get_cover_letter_endpoint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    tailoring_service: ResumeTailoringService = Depends(get_resume_tailoring_service),
) -> CoverLetterResponse:
    result = await tailoring_service.get_cover_letter(
        user_id=current_user.id,
        session_id=session_id,
    )
    return CoverLetterResponse.model_validate(result)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tailoring Session",
    description="Delete a tailoring session owned by the authenticated user.",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Tailoring session not found"},
    },
)
async def delete_tailoring_session_endpoint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    tailoring_service: ResumeTailoringService = Depends(get_resume_tailoring_service),
) -> Response:
    await tailoring_service.delete_session(
        user_id=current_user.id,
        session_id=session_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@export_router.get(
    "/resume/{version_id}",
    summary="Export Tailored Resume",
    description="Export a tailored resume version as markdown, docx, or pdf.",
    responses=_EXPORT_RESPONSES,
)
async def export_resume_endpoint(
    version_id: UUID,
    format: str = Query(
        default="md",
        examples=["md", "docx", "pdf"],
        description="Export file format: md, docx, or pdf.",
    ),
    _: None = Depends(
        limit(
            bucket="export_resume",
            requests=settings.rate_limit_export_requests,
        )
    ),
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> FileResponse:
    file_path = await export_service.export_resume(
        user_id=current_user.id,
        version_id=version_id,
        format=format,
    )
    return FileResponse(path=file_path, filename=Path(file_path).name)


@export_router.get(
    "/cover-letter/{cover_letter_id}",
    summary="Export Cover Letter",
    description="Export a generated cover letter as markdown, docx, or pdf.",
    responses=_EXPORT_RESPONSES,
)
async def export_cover_letter_endpoint(
    cover_letter_id: UUID,
    format: str = Query(
        default="md",
        examples=["md", "docx", "pdf"],
        description="Export file format: md, docx, or pdf.",
    ),
    _: None = Depends(
        limit(
            bucket="export_cover_letter",
            requests=settings.rate_limit_export_requests,
        )
    ),
    current_user: User = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
) -> FileResponse:
    file_path = await export_service.export_cover_letter(
        user_id=current_user.id,
        cover_letter_id=cover_letter_id,
        format=format,
    )
    return FileResponse(path=file_path, filename=Path(file_path).name)
