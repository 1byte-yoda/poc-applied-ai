"""Pydantic response schemas for the learning platform API."""

from app.schemas.content import ErrorResponse
from app.schemas.course import (
    CourseDetailResponse,
    CourseResponse,
    ModuleResponse,
    SectionResponse,
)
from app.schemas.lecture import LectureMetadataResponse, LectureResponse
from app.schemas.progress import (
    BatchProgressResponse,
    CourseProgressResponse,
    LectureCompleteResponse,
)

__all__ = [
    "CourseResponse",
    "CourseDetailResponse",
    "ModuleResponse",
    "SectionResponse",
    "LectureResponse",
    "LectureMetadataResponse",
    "ErrorResponse",
    "LectureCompleteResponse",
    "CourseProgressResponse",
    "BatchProgressResponse",
]
