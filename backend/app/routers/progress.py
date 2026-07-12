"""Progress tracking API endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
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


@router.put(
    "/progress/lectures/{lecture_id}/position",
    summary="Save playback position for a lecture",
)
async def save_playback_position(
    lecture_id: int,
    position: float,
    session: AsyncSession = Depends(get_session),
):
    """Save the current playback position (in seconds) for a video lecture."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.models import Lecture, PlaybackPosition

    # Verify lecture exists
    result = await session.execute(
        select(Lecture.id).where(Lecture.id == lecture_id)
    )
    if result.scalar_one_or_none() is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Lecture with id {lecture_id} not found")

    stmt = (
        pg_insert(PlaybackPosition)
        .values(lecture_id=lecture_id, position_seconds=position)
        .on_conflict_do_update(
            index_elements=["lecture_id"],
            set_={"position_seconds": position},
        )
    )
    await session.execute(stmt)
    await session.commit()
    return {"lecture_id": lecture_id, "position_seconds": position}


@router.get(
    "/progress/lectures/{lecture_id}/position",
    summary="Get playback position for a lecture",
)
async def get_playback_position(
    lecture_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get the saved playback position (in seconds) for a video lecture."""
    from sqlalchemy import select as sa_select

    from app.models import PlaybackPosition

    result = await session.execute(
        sa_select(PlaybackPosition.position_seconds).where(
            PlaybackPosition.lecture_id == lecture_id
        )
    )
    position = result.scalar_one_or_none()
    return {"lecture_id": lecture_id, "position_seconds": position or 0.0}


@router.delete(
    "/progress/lectures/{lecture_id}/position",
    summary="Clear playback position for a lecture",
)
async def clear_playback_position(
    lecture_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Clear the saved playback position (e.g., when video completes)."""
    from sqlalchemy import delete

    from app.models import PlaybackPosition

    await session.execute(
        delete(PlaybackPosition).where(PlaybackPosition.lecture_id == lecture_id)
    )
    await session.commit()
    return {"lecture_id": lecture_id, "cleared": True}
