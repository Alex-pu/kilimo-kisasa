"""Add expert applications

Revision ID: 004_expert_applications
Revises: 003_issue_post_type
Create Date: 2026-06-10 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "004_expert_applications"
down_revision: Union[str, None] = "003_issue_post_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


application_status_enum = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="expertapplicationstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    application_status_enum.create(bind, checkfirst=True)
    op.create_table(
        "expert_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("linkedin_url", sa.String(length=500), nullable=False),
        sa.Column("education", sa.Text(), nullable=False),
        sa.Column("credentials", sa.Text(), nullable=True),
        sa.Column("experience_summary", sa.Text(), nullable=True),
        sa.Column("status", application_status_enum, nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expert_applications_created_at", "expert_applications", ["created_at"])
    op.create_index("ix_expert_applications_status", "expert_applications", ["status"])
    op.create_index("ix_expert_applications_user_id", "expert_applications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_expert_applications_user_id", table_name="expert_applications")
    op.drop_index("ix_expert_applications_status", table_name="expert_applications")
    op.drop_index("ix_expert_applications_created_at", table_name="expert_applications")
    op.drop_table("expert_applications")
    application_status_enum.drop(op.get_bind(), checkfirst=True)
