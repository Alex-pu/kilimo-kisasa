"""Add local password hashes

Revision ID: 007_user_password_hash
Revises: 006_issue_votes
Create Date: 2026-06-10 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007_user_password_hash"
down_revision: Union[str, None] = "006_issue_votes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
