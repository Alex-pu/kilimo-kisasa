"""Add issue votes

Revision ID: 006_issue_votes
Revises: 005_agrovet_owner_catalogue
Create Date: 2026-06-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "006_issue_votes"
down_revision: Union[str, None] = "005_agrovet_owner_catalogue"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "issue_votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issue_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_id", "user_id", name="uq_issue_votes_issue_user"),
    )
    op.create_index("ix_issue_votes_issue_id", "issue_votes", ["issue_id"])
    op.create_index("ix_issue_votes_user_id", "issue_votes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_issue_votes_user_id", table_name="issue_votes")
    op.drop_index("ix_issue_votes_issue_id", table_name="issue_votes")
    op.drop_table("issue_votes")
