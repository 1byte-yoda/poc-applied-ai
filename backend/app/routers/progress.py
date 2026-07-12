"""Progress tracking API endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.content import ErrorResponse
from app.schemas.progress import (
    BatchProgressResponse,
    CourseProgressResponse,
    LectureCompleteResponse,
)
from app.services.progress_service import ProgressService

router = APIRouter(tags=["progress"])


@router.post(
    "/progress/lectures/{lecture_id}/complete",
    response_model=LectureCompleteResponse,
    responses={
        404: {"model": ErrorResponse},
        503: {"description": "Service temporarily unavailable"},
    },
    summary="Mark a lecture as complete",
)
async def mark_lecture_complete(
    lecture_id: int,
    session: AsyncSession = Depends(get_session),
) -> LectureCompleteResponse:
    """Mark a lecture as completed. Idempotent — returns existing record if already complete."""
    try:
        service = ProgressService(session)
        result = await service.mark_lecture_complete(lecture_id)
        return LectureCompleteResponse(
            lecture_id=result.lecture_id,
            completed_at=result.completed_at,
        )
    except OSError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable. Please retry later."},
            headers={"Retry-After": "30"},
        )


@router.get(
    "/progress/courses/{course_id}",
    response_model=CourseProgressResponse,
    responses={
        404: {"model": ErrorResponse},
        503: {"description": "Service temporarily unavailable"},
    },
    summary="Get progress for a single course",
)
async def get_course_progress(
    course_id: int,
    session: AsyncSession = Depends(get_session),
) -> CourseProgressResponse:
    """Return progress data for a single course including completed lecture IDs."""
    try:
        service = ProgressService(session)
        result = await service.get_course_progress(course_id)
        return CourseProgressResponse(
            course_id=result.course_id,
            percentage=result.percentage,
            completed_count=result.completed_count,
            total_count=result.total_count,
            completed_lecture_ids=result.completed_lecture_ids,
        )
    except OSError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable. Please retry later."},
            headers={"Retry-After": "30"},
        )


@router.get(
    "/progress/courses",
    response_model=BatchProgressResponse,
    responses={
        503: {"description": "Service temporarily unavailable"},
    },
    summary="Get progress for all courses",
)
async def get_batch_progress(
    session: AsyncSession = Depends(get_session),
) -> BatchProgressResponse:
    """Return progress percentages for all courses."""
    try:
        service = ProgressService(session)
        progress_map = await service.get_batch_progress()
        return BatchProgressResponse(progress=progress_map)
    except OSError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable. Please retry later."},
            headers={"Retry-After": "30"},
        )


@router.delete(
    "/progress/lectures/{lecture_id}/complete",
    responses={
        404: {"model": ErrorResponse},
        503: {"description": "Service temporarily unavailable"},
    },
    summary="Unmark a lecture as complete",
)
async def unmark_lecture_complete(
    lecture_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove completion status from a lecture."""
    try:
        service = ProgressService(session)
        deleted = await service.unmark_lecture_complete(lecture_id)
        return {"lecture_id": lecture_id, "was_completed": deleted}
    except OSError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable. Please retry later."},
            headers={"Retry-After": "30"},
        )
