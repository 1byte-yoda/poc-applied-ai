"""Lecture SQLAlchemy ORM model."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.course import Base


class Lecture(Base):
    """Represents a lecture (content item) within a section."""

    __tablename__ = "lectures"
    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_lecture_section_order"),
        Index("idx_lectures_content_type", "content_type"),
        Index("idx_lectures_section_id", "section_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    section: Mapped["Section"] = relationship("Section", back_populates="lectures")

    def __repr__(self) -> str:
        return (
            f"<Lecture(id={self.id}, title='{self.title}', "
            f"type='{self.content_type}', order={self.order_index})>"
        )


from app.models.section import Section  # noqa: E402, F401
