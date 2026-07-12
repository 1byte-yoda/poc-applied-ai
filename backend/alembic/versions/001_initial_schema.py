"""Initial schema - create all tables.

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- courses ---
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- modules ---
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("course_id", "order_index", name="uq_module_course_order"),
    )

    # --- sections ---
    op.create_table(
        "sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "module_id",
            sa.Integer(),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("module_id", "order_index", name="uq_section_module_order"),
    )

    # --- lectures ---
    op.create_table(
        "lectures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "section_id",
            sa.Integer(),
            sa.ForeignKey("sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_type", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "section_id", "order_index", name="uq_lecture_section_order"
        ),
    )

    # Indexes on lectures
    op.create_index("idx_lectures_content_type", "lectures", ["content_type"])
    op.create_index("idx_lectures_section_id", "lectures", ["section_id"])

    # --- colab_mappings ---
    op.create_table(
        "colab_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(500), nullable=False, unique=True),
        sa.Column("local_path", sa.String(1000), nullable=False),
        sa.Column("google_drive_file_id", sa.String(255), nullable=True),
        sa.Column("colab_url", sa.String(1000), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Index on colab_mappings filename (already unique but explicit for clarity)
    op.create_index("idx_colab_mappings_filename", "colab_mappings", ["filename"])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respects foreign key dependencies)
    op.drop_index("idx_colab_mappings_filename", table_name="colab_mappings")
    op.drop_table("colab_mappings")

    op.drop_index("idx_lectures_section_id", table_name="lectures")
    op.drop_index("idx_lectures_content_type", table_name="lectures")
    op.drop_table("lectures")

    op.drop_table("sections")
    op.drop_table("modules")
    op.drop_table("courses")
