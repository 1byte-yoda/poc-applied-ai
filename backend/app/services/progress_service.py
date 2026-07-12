"""Progress tracking service — business logic for lecture completion and course progress."""

import math
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, Lecture, LectureProgress, Module, Section


@dataclass
class LectureCompletionResult:
    """Result of marking a lecture as complete."""

    lecture_id: int
    completed_at: datetime
    already_existed: bool


@dataclass
class CourseProgressResult:
    """Progress data for a single course."""

    course_id: int
    percentage: int
    completed_count: int
    total_count: int
    completed_lecture_ids: list[int]


class ProgressService:
    """Encapsulates all progress business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def mark_lecture_complete(self, lecture_id: int) -> LectureCompletionResult:
        """Mark a lecture as completed. Idempotent — returns existing record if already complete.

        Raises HTTPException(404) if the lecture does not exist.
        """
        # Verify the lecture exists
        lecture_result = await self.session.execute(
            select(Lecture.id).where(Lecture.id == lecture_id)
        )
        if lecture_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=404,
                detail=f"Lecture with id {lecture_id} not found",
            )

        # INSERT ... ON CONFLICT (lecture_id) DO NOTHING for idempotency
        stmt = (
            pg_insert(LectureProgress)
            .values(lecture_id=lecture_id)
            .on_conflict_do_nothing(index_elements=["lecture_id"])
            .returning(LectureProgress.lecture_id, LectureProgress.completed_at)
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is not None:
            # Newly inserted
            await self.session.commit()
            return LectureCompletionResult(
                lecture_id=row.lecture_id,
                completed_at=row.completed_at,
                already_existed=False,
            )

        # Already existed — fetch the existing record
        existing_result = await self.session.execute(
            select(LectureProgress.lecture_id, LectureProgress.completed_at).where(
                LectureProgress.lecture_id == lecture_id
            )
        )
        existing = existing_result.one()
        return LectureCompletionResult(
            lecture_id=existing.lecture_id,
            completed_at=existing.completed_at,
            already_existed=True,
        )

    async def get_course_progress(self, course_id: int) -> CourseProgressResult:
        """Get progress for a single course including the set of completed lecture IDs.

        Raises HTTPException(404) if the course does not exist.
        """
        # Verify the course exists
        course_result = await self.session.execute(
            select(Course.id).where(Course.id == course_id)
        )
        if course_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=404,
                detail=f"Course with id {course_id} not found",
            )

        # Join modules → sections → lectures, LEFT JOIN lecture_progress
        # Get total lectures and completed lecture IDs
        stmt = (
            select(Lecture.id, LectureProgress.id.label("progress_id"))
            .join(Section, Lecture.section_id == Section.id)
            .join(Module, Section.module_id == Module.id)
            .outerjoin(LectureProgress, LectureProgress.lecture_id == Lecture.id)
            .where(Module.course_id == course_id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        total_count = len(rows)
        completed_lecture_ids = [row.id for row in rows if row.progress_id is not None]
        completed_count = len(completed_lecture_ids)
        percentage = self.calculate_percentage(completed_count, total_count)

        return CourseProgressResult(
            course_id=course_id,
            percentage=percentage,
            completed_count=completed_count,
            total_count=total_count,
            completed_lecture_ids=completed_lecture_ids,
        )

    async def get_batch_progress(self) -> dict[int, int]:
        """Get progress percentages for all courses. Returns {course_id: percentage}."""
        stmt = (
            select(
                Module.course_id,
                func.count(Lecture.id).label("total_lectures"),
                func.count(LectureProgress.id).label("completed_lectures"),
            )
            .join(Section, Lecture.section_id == Section.id)
            .join(Module, Section.module_id == Module.id)
            .outerjoin(LectureProgress, LectureProgress.lecture_id == Lecture.id)
            .group_by(Module.course_id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        progress_map: dict[int, int] = {}
        for row in rows:
            progress_map[row.course_id] = self.calculate_percentage(
                row.completed_lectures, row.total_lectures
            )

        # Include courses that have no lectures (0%)
        all_courses_result = await self.session.execute(select(Course.id))
        all_course_ids = [row[0] for row in all_courses_result.all()]
        for course_id in all_course_ids:
            if course_id not in progress_map:
                progress_map[course_id] = 0

        return progress_map

    @staticmethod
    def calculate_percentage(completed: int, total: int) -> int:
        """Calculate progress percentage as floor(completed/total*100).

        Returns 0 when total is 0. Result is always in [0, 100].
        """
        if total <= 0:
            return 0
        result = math.floor(completed / total * 100)
        # Clamp to [0, 100] for safety
        return max(0, min(100, result))
