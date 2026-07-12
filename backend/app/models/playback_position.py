"""PlaybackPosition SQLAlchemy ORM model — stores video resume timestamp."""

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.course import Base


class PlaybackPosition(Base):
    """Stores the last playback position for a lecture (for resume functionality)."""

    __tablename__ = "playback_positions"
    __table_args__ = (
        UniqueConstraint("lecture_id", name="uq_playback_positions_lecture_id"),
        Index("idx_playback_positions_lecture_id", "lecture_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    position_seconds: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
