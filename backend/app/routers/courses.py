"""Course browsing API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Course, Lecture, Module, Section
from app.schemas.content import ErrorResponse
from app.schemas.course import (
    CourseDetailResponse,
    CourseResponse,
    ModuleListResponse,
    ModuleResponse,
    SectionDetailResponse,
    SectionListResponse,
    SectionResponse,
)
from app.schemas.lecture import LectureResponse

router = APIRouter(tags=["courses"])


@router.get(
    "/courses",
    response_model=list[CourseResponse],
    summary="List all courses",
)
async def list_courses(
    session: AsyncSession = Depends(get_session),
) -> list[CourseResponse]:
    """Return all courses with title, description, module count, and lecture count."""
    # Subquery for module count
    module_count_subq = (
        select(
            Module.course_id,
            func.count(Module.id).label("module_count"),
        )
        .group_by(Module.course_id)
        .subquery()
    )

    # Subquery for lecture count (lectures are nested via section → module → course)
    lecture_count_subq = (
        select(
            Module.course_id,
            func.count(Lecture.id).label("lecture_count"),
        )
        .join(Section, Section.module_id == Module.id)
        .join(Lecture, Lecture.section_id == Section.id)
        .group_by(Module.course_id)
        .subquery()
    )

    result = await session.execute(
        select(
            Course,
            func.coalesce(module_count_subq.c.module_count, 0).label("module_count"),
            func.coalesce(lecture_count_subq.c.lecture_count, 0).label("lecture_count"),
        )
        .outerjoin(module_count_subq, Course.id == module_count_subq.c.course_id)
        .outerjoin(lecture_count_subq, Course.id == lecture_count_subq.c.course_id)
        .order_by(Course.id)
    )

    rows = result.all()
    return [
        CourseResponse(
            id=row.Course.id,
            title=row.Course.title,
            description=row.Course.description,
            module_count=row.module_count,
            lecture_count=row.lecture_count,
        )
        for row in rows
    ]


@router.get(
    "/courses/{course_id}",
    response_model=CourseDetailResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get course detail with full nested structure",
)
async def get_course_detail(
    course_id: int,
    session: AsyncSession = Depends(get_session),
) -> CourseDetailResponse:
    """Return a course with full nested structure (modules → sections → lectures)."""
    result = await session.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.modules)
            .selectinload(Module.sections)
            .selectinload(Section.lectures)
        )
    )
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(status_code=404, detail=f"Course with id {course_id} not found")

    # Count totals
    total_lectures = sum(
        len(section.lectures)
        for module in course.modules
        for section in module.sections
    )

    modules_response = [
        ModuleResponse(
            id=module.id,
            title=module.title,
            order=module.order_index,
            sections=[
                SectionResponse(
                    id=section.id,
                    title=section.title,
                    order=section.order_index,
                    lectures=[
                        LectureResponse(
                            id=lecture.id,
                            title=lecture.title,
                            order=lecture.order_index,
                            content_type=lecture.content_type,
                            file_path=lecture.file_path,
                            colab_url=None,
                            duration_seconds=lecture.duration_seconds,
                        )
                        for lecture in section.lectures
                    ],
                )
                for section in module.sections
            ],
        )
        for module in course.modules
    ]

    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        module_count=len(course.modules),
        lecture_count=total_lectures,
        modules=modules_response,
    )


@router.get(
    "/courses/{course_id}/modules",
    response_model=list[ModuleListResponse],
    responses={404: {"model": ErrorResponse}},
    summary="List modules for a course with aggregate counts",
)
async def list_modules_for_course(
    course_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[ModuleListResponse]:
    """Return modules for a course with section_count and lecture_count."""
    # Verify course exists
    course = await session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course with id {course_id} not found")

    result = await session.execute(
        select(
            Module,
            func.count(distinct(Section.id)).label("section_count"),
            func.count(Lecture.id).label("lecture_count"),
        )
        .where(Module.course_id == course_id)
        .outerjoin(Section, Section.module_id == Module.id)
        .outerjoin(Lecture, Lecture.section_id == Section.id)
        .group_by(Module.id)
        .order_by(Module.order_index)
    )

    return [
        ModuleListResponse(
            id=row.Module.id,
            title=row.Module.title,
            order=row.Module.order_index,
            section_count=row.section_count,
            lecture_count=row.lecture_count,
        )
        for row in result.all()
    ]


@router.get(
    "/modules/{module_id}/sections",
    response_model=list[SectionListResponse],
    responses={404: {"model": ErrorResponse}},
    summary="List sections for a module with lecture counts",
)
async def list_sections_for_module(
    module_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[SectionListResponse]:
    """Return sections for a module with lecture_count."""
    # Verify module exists
    module = await session.get(Module, module_id)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module with id {module_id} not found")

    result = await session.execute(
        select(
            Section,
            func.count(Lecture.id).label("lecture_count"),
        )
        .where(Section.module_id == module_id)
        .outerjoin(Lecture, Lecture.section_id == Section.id)
        .group_by(Section.id)
        .order_by(Section.order_index)
    )

    return [
        SectionListResponse(
            id=row.Section.id,
            title=row.Section.title,
            order=row.Section.order_index,
            lecture_count=row.lecture_count,
        )
        for row in result.all()
    ]


@router.get(
    "/sections/{section_id}",
    response_model=SectionDetailResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get section detail with lectures and breadcrumb context",
)
async def get_section_detail(
    section_id: int,
    session: AsyncSession = Depends(get_session),
) -> SectionDetailResponse:
    """Return a section with its lectures and parent module/course context."""
    result = await session.execute(
        select(Section)
        .where(Section.id == section_id)
        .options(
            selectinload(Section.lectures),
            selectinload(Section.module).selectinload(Module.course),
        )
    )
    section = result.scalar_one_or_none()

    if section is None:
        raise HTTPException(status_code=404, detail=f"Section with id {section_id} not found")

    return SectionDetailResponse(
        id=section.id,
        title=section.title,
        module_id=section.module.id,
        module_title=section.module.title,
        course_id=section.module.course.id,
        course_title=section.module.course.title,
        lectures=[
            LectureResponse(
                id=lec.id,
                title=lec.title,
                order=lec.order_index,
                content_type=lec.content_type,
                file_path=lec.file_path,
                colab_url=None,
                duration_seconds=lec.duration_seconds,
            )
            for lec in sorted(section.lectures, key=lambda l: l.order_index)
        ],
    )
