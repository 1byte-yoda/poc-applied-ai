"""Pydantic response schemas for course-related endpoints."""

from pydantic import BaseModel

from app.schemas.lecture import LectureResponse


class SectionResponse(BaseModel):
    """Response schema for a section within a module."""

    id: int
    title: str
    order: int
    lectures: list[LectureResponse]


class ModuleResponse(BaseModel):
    """Response schema for a module within a course."""

    id: int
    title: str
    order: int
    sections: list[SectionResponse]


class CourseResponse(BaseModel):
    """Response schema for course listing."""

    id: int
    title: str
    description: str | None = None
    module_count: int
    lecture_count: int


class CourseDetailResponse(CourseResponse):
    """Response schema for course detail with full nested structure."""

    modules: list[ModuleResponse]
