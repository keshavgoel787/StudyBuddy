"""add assignments table

Revision ID: e3af5cd40a0c
Revises: a037f8283f46
Create Date: 2025-11-06 00:50:58.918904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3af5cd40a0c'
down_revision: Union[str, None] = 'a037f8283f46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_id'), 'assignments', ['id'], unique=False)
    op.create_index(op.f('ix_assignments_user_id'), 'assignments', ['user_id'], unique=False)
    op.create_index(op.f('ix_assignments_due_date'), 'assignments', ['due_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_assignments_due_date'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_user_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_id'), table_name='assignments')
    op.drop_table('assignments')
