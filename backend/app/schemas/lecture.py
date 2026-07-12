"""Pydantic response schemas for lecture-related endpoints."""

from pydantic import BaseModel


class LectureResponse(BaseModel):
    """Response schema for a lecture."""

    id: int
    title: str
    order: int
    content_type: str
    file_path: str | None = None
    colab_url: str | None = None
    duration_seconds: int | None = None


class LectureMetadataResponse(BaseModel):
    """Response schema for lecture metadata (without order/duration)."""

    id: int
    title: str
    content_type: str
    file_path: str | None = None
    colab_url: str | None = None
