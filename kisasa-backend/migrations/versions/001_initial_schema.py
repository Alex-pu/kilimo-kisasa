"""Initial schema - create all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-05-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('firebase_uid', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('farmer', 'expert', 'agrovet', 'admin', name='userrole'), nullable=False),
        sa.Column('bio', sa.String(500), nullable=True),
        sa.Column('profile_pic_url', sa.String(), nullable=True),
        sa.Column('location_latitude', sa.Float(), nullable=True),
        sa.Column('location_longitude', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(), nullable=True),
        sa.Column('verification_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('firebase_uid'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'])

    # Create issues table
    op.create_table(
        'issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('crop_disease', 'pest_management', 'soil_health', 'water_management', 'fertilizer', 'seed_quality', 'weather', 'market_price', 'other', name='issuecategory'), nullable=False),
        sa.Column('status', sa.Enum('open', 'in_progress', 'resolved', 'closed', name='issuestatus'), nullable=False, server_default='open'),
        sa.Column('image_urls', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('location_latitude', sa.Float(), nullable=True),
        sa.Column('location_longitude', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_urgent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_issues_category', 'issues', ['category'])
    op.create_index('ix_issues_creator_id', 'issues', ['creator_id'])
    op.create_index('ix_issues_created_at', 'issues', ['created_at'])
    op.create_index('ix_issues_status', 'issues', ['status'])

    # Create comments table
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_urls', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comments_author_id', 'comments', ['author_id'])
    op.create_index('ix_comments_created_at', 'comments', ['created_at'])
    op.create_index('ix_comments_issue_id', 'comments', ['issue_id'])

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('farm_input_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('linked_product_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
        sa.ForeignKeyConstraint(['recommender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recommendations_created_at', 'recommendations', ['created_at'])
    op.create_index('ix_recommendations_issue_id', 'recommendations', ['issue_id'])
    op.create_index('ix_recommendations_recommender_id', 'recommendations', ['recommender_id'])

    # Create agrovets table
    op.create_table(
        'agrovets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('location_latitude', sa.Float(), nullable=False),
        sa.Column('location_longitude', sa.Float(), nullable=False),
        sa.Column('location_name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('verification_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('profile_image_url', sa.String(), nullable=True),
        sa.Column('cover_image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agrovets_created_at', 'agrovets', ['created_at'])
    op.create_index('ix_agrovets_name', 'agrovets', ['name'])

    # Create agrovet_products table
    op.create_table(
        'agrovet_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agrovet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='KES'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agrovet_id'], ['agrovets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agrovet_products_agrovet_id', 'agrovet_products', ['agrovet_id'])
    op.create_index('ix_agrovet_products_product_name', 'agrovet_products', ['product_name'])

    # Create expert_endorsements table
    op.create_table(
        'expert_endorsements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expert_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agrovet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agrovet_id'], ['agrovets.id'], ),
        sa.ForeignKeyConstraint(['expert_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expert_endorsements_agrovet_id', 'expert_endorsements', ['agrovet_id'])
    op.create_index('ix_expert_endorsements_expert_id', 'expert_endorsements', ['expert_id'])


def downgrade() -> None:
    op.drop_index('ix_expert_endorsements_expert_id', table_name='expert_endorsements')
    op.drop_index('ix_expert_endorsements_agrovet_id', table_name='expert_endorsements')
    op.drop_table('expert_endorsements')
    op.drop_index('ix_agrovet_products_product_name', table_name='agrovet_products')
    op.drop_index('ix_agrovet_products_agrovet_id', table_name='agrovet_products')
    op.drop_table('agrovet_products')
    op.drop_index('ix_agrovets_name', table_name='agrovets')
    op.drop_index('ix_agrovets_created_at', table_name='agrovets')
    op.drop_table('agrovets')
    op.drop_index('ix_recommendations_recommender_id', table_name='recommendations')
    op.drop_index('ix_recommendations_issue_id', table_name='recommendations')
    op.drop_index('ix_recommendations_created_at', table_name='recommendations')
    op.drop_table('recommendations')
    op.drop_index('ix_comments_issue_id', table_name='comments')
    op.drop_index('ix_comments_created_at', table_name='comments')
    op.drop_index('ix_comments_author_id', table_name='comments')
    op.drop_table('comments')
    op.drop_index('ix_issues_status', table_name='issues')
    op.drop_index('ix_issues_created_at', table_name='issues')
    op.drop_index('ix_issues_creator_id', table_name='issues')
    op.drop_index('ix_issues_category', table_name='issues')
    op.drop_table('issues')
    op.drop_index('ix_users_firebase_uid', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
