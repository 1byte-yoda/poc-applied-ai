"""Lecture API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ColabMapping, Lecture
from app.schemas.content import ErrorResponse
from app.schemas.lecture import LectureMetadataResponse
from app.services.content_resolver import resolve_lecture_content

router = APIRouter(tags=["lectures"])


@router.get(
    "/lectures/{lecture_id}",
    response_model=LectureMetadataResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get lecture metadata",
)
async def get_lecture_metadata(
    lecture_id: int,
    session: AsyncSession = Depends(get_session),
) -> LectureMetadataResponse:
    """Return lecture metadata: title, content_type, file_path, and colab_url if applicable."""
    result = await session.execute(
        select(Lecture).where(Lecture.id == lecture_id)
    )
    lecture = result.scalar_one_or_none()

    if lecture is None:
        raise HTTPException(status_code=404, detail=f"Lecture with id {lecture_id} not found")

    # Look up Colab URL if this is a notebook
    colab_url: str | None = None
    if lecture.content_type == "ipynb" and lecture.original_filename:
        mapping_result = await session.execute(
            select(ColabMapping).where(
                ColabMapping.filename == lecture.original_filename
            )
        )
        mapping = mapping_result.scalar_one_or_none()
        if mapping:
            colab_url = mapping.colab_url

    return LectureMetadataResponse(
        id=lecture.id,
        title=lecture.title,
        content_type=lecture.content_type,
        file_path=lecture.file_path,
        colab_url=colab_url,
    )


@router.get(
    "/lectures/{lecture_id}/content",
    response_model=None,
    responses={
        404: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
    },
    summary="Get lecture content",
)
async def get_lecture_content(
    lecture_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Serve lecture content based on its type.

    - mp4/pdf/mp3: Streaming file response
    - ipynb: HTTP 307 redirect to Colab URL
    - docx: Converted to HTML
    - txt: Wrapped in preformatted HTML template
    """
    return await resolve_lecture_content(lecture_id, session)
