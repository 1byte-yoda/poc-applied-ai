"""LectureProgress SQLAlchemy ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.course import Base


class LectureProgress(Base):
    """Records that a lecture has been completed."""

    __tablename__ = "lecture_progress"
    __table_args__ = (
        UniqueConstraint("lecture_id", name="uq_lecture_progress_lecture_id"),
        Index("idx_lecture_progress_lecture_id", "lecture_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    lecture: Mapped["Lecture"] = relationship("Lecture")

    def __repr__(self) -> str:
        return (
            f"<LectureProgress(id={self.id}, lecture_id={self.lecture_id}, "
            f"completed_at={self.completed_at})>"
        )


from app.models.lecture import Lecture  # noqa: E402, F401
