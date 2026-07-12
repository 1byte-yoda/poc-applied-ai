"""ColabMapping SQLAlchemy ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.course import Base


class ColabMapping(Base):
    """Maps .ipynb filenames to their Google Colab URLs."""

    __tablename__ = "colab_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    local_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    google_drive_file_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    colab_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ColabMapping(id={self.id}, filename='{self.filename}')>"
