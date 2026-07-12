"""Pydantic response schemas for error/content responses."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str
