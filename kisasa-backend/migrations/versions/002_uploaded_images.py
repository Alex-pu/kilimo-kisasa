"""Add uploaded images table

Revision ID: 002_uploaded_images
Revises: 001_initial_schema
Create Date: 2026-06-10 16:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "002_uploaded_images"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uploaded_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index("ix_uploaded_images_created_at", "uploaded_images", ["created_at"])
    op.create_index("ix_uploaded_images_issue_id", "uploaded_images", ["issue_id"])
    op.create_index("ix_uploaded_images_uploaded_by_id", "uploaded_images", ["uploaded_by_id"])


def downgrade() -> None:
    op.drop_index("ix_uploaded_images_uploaded_by_id", table_name="uploaded_images")
    op.drop_index("ix_uploaded_images_issue_id", table_name="uploaded_images")
    op.drop_index("ix_uploaded_images_created_at", table_name="uploaded_images")
    op.drop_table("uploaded_images")
