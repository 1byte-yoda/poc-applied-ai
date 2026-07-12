"""Module SQLAlchemy ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.course import Base


class Module(Base):
    """Represents a module (semester/topic group) within a course."""

    __tablename__ = "modules"
    __table_args__ = (
        UniqueConstraint("course_id", "order_index", name="uq_module_course_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    sections: Mapped[list["Section"]] = relationship(
        "Section",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Section.order_index",
    )

    def __repr__(self) -> str:
        return f"<Module(id={self.id}, title='{self.title}', order={self.order_index})>"


from app.models.course import Course  # noqa: E402, F401
from app.models.section import Section  # noqa: E402, F401
