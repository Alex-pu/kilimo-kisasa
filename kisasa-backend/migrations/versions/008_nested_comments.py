"""Add nested comments

Revision ID: 008_nested_comments
Revises: 007_user_password_hash
Create Date: 2026-06-17 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "008_nested_comments"
down_revision: Union[str, None] = "007_user_password_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("parent_comment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_comments_parent_comment_id_comments",
        "comments",
        "comments",
        ["parent_comment_id"],
        ["id"],
    )
    op.create_index(
        "ix_comments_parent_comment_id",
        "comments",
        ["parent_comment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_comments_parent_comment_id", table_name="comments")
    op.drop_constraint(
        "fk_comments_parent_comment_id_comments",
        "comments",
        type_="foreignkey",
    )
    op.drop_column("comments", "parent_comment_id")
