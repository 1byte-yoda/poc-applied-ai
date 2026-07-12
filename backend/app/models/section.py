"""Section SQLAlchemy ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.course import Base


class Section(Base):
    """Represents a section (chapter) within a module."""

    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("module_id", "order_index", name="uq_section_module_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    module: Mapped["Module"] = relationship("Module", back_populates="sections")
    lectures: Mapped[list["Lecture"]] = relationship(
        "Lecture",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Lecture.order_index",
    )

    def __repr__(self) -> str:
        return f"<Section(id={self.id}, title='{self.title}', order={self.order_index})>"


from app.models.lecture import Lecture  # noqa: E402, F401
from app.models.module import Module  # noqa: E402, F401
