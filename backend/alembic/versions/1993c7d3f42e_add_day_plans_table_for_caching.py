"""Add day_plans table for caching

Revision ID: 1993c7d3f42e
Revises: 251daabca771
Create Date: 2025-11-04 23:06:00.217944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1993c7d3f42e'
down_revision: Union[str, None] = '251daabca771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create day_plans table
    op.create_table(
        'day_plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('events', sa.JSON(), nullable=False),
        sa.Column('free_blocks', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Create index on user_id and date for fast lookups
    op.create_index('ix_day_plans_user_date', 'day_plans', ['user_id', 'date'], unique=True)


def downgrade() -> None:
    # Drop index and table
    op.drop_index('ix_day_plans_user_date', table_name='day_plans')
    op.drop_table('day_plans')
