"""Pydantic response schemas for progress tracking endpoints."""

from datetime import datetime

from pydantic import BaseModel


class LectureCompleteResponse(BaseModel):
    """Response schema for marking a lecture as complete."""

    lecture_id: int
    completed_at: datetime


class CourseProgressResponse(BaseModel):
    """Response schema for single course progress."""

    course_id: int
    percentage: int
    completed_count: int
    total_count: int
    completed_lecture_ids: list[int]


class BatchProgressResponse(BaseModel):
    """Response schema for batch progress across all courses."""

    progress: dict[int, int]  # course_id -> percentage
