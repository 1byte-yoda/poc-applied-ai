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


class ModuleListResponse(BaseModel):
    """Module card in the specialization detail page."""

    id: int
    title: str
    order: int
    section_count: int
    lecture_count: int


class SectionListResponse(BaseModel):
    """Section card in the module detail page."""

    id: int
    title: str
    order: int
    lecture_count: int


class SectionDetailResponse(BaseModel):
    """Section with lectures for the content viewer."""

    id: int
    title: str
    module_id: int
    module_title: str
    course_id: int
    course_title: str
    lectures: list[LectureResponse]
