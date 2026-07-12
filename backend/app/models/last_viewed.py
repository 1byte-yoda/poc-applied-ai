"""LastViewed SQLAlchemy ORM model — tracks the last viewed lecture per course."""

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.course import Base


class LastViewed(Base):
    """Stores the last viewed lecture for each course (for auto-resume on revisit)."""

    __tablename__ = "last_viewed"
    __table_args__ = (
        UniqueConstraint("course_id", name="uq_last_viewed_course_id"),
        Index("idx_last_viewed_course_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    lecture_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lectures.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
