"""Add lecture_progress table.

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lecture_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "lecture_id",
            sa.Integer(),
            sa.ForeignKey("lectures.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("lecture_id", name="uq_lecture_progress_lecture_id"),
    )

    op.create_index(
        "idx_lecture_progress_lecture_id", "lecture_progress", ["lecture_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_lecture_progress_lecture_id", table_name="lecture_progress")
    op.drop_table("lecture_progress")
