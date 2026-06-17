"""Add issue post type

Revision ID: 003_issue_post_type
Revises: 002_uploaded_images
Create Date: 2026-06-10 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_issue_post_type"
down_revision: Union[str, None] = "002_uploaded_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


post_type_enum = sa.Enum("issue", "educational", "farming_news", name="posttype")


def upgrade() -> None:
    bind = op.get_bind()
    post_type_enum.create(bind, checkfirst=True)
    op.add_column(
        "issues",
        sa.Column(
            "post_type",
            post_type_enum,
            nullable=False,
            server_default="issue",
        ),
    )
    op.create_index("ix_issues_post_type", "issues", ["post_type"])
    op.alter_column("issues", "post_type", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_issues_post_type", table_name="issues")
    op.drop_column("issues", "post_type")
    post_type_enum.drop(op.get_bind(), checkfirst=True)
