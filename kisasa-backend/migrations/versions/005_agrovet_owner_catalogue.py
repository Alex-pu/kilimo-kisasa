"""Add agrovet ownership and product instructions

Revision ID: 005_agrovet_owner_catalogue
Revises: 004_expert_applications
Create Date: 2026-06-10 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "005_agrovet_owner_catalogue"
down_revision: Union[str, None] = "004_expert_applications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agrovets", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("agrovets", sa.Column("contact_person_name", sa.String(length=255), nullable=True))
    op.create_index("ix_agrovets_owner_id", "agrovets", ["owner_id"])
    op.create_foreign_key("fk_agrovets_owner_id_users", "agrovets", "users", ["owner_id"], ["id"])

    op.add_column("agrovet_products", sa.Column("instructions", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("agrovet_products", "instructions")
    op.drop_constraint("fk_agrovets_owner_id_users", "agrovets", type_="foreignkey")
    op.drop_index("ix_agrovets_owner_id", table_name="agrovets")
    op.drop_column("agrovets", "contact_person_name")
    op.drop_column("agrovets", "owner_id")
