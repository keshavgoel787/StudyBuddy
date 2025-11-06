"""add_bus_schedule_and_preferences_tables

Revision ID: a037f8283f46
Revises: add_perf_indexes
Create Date: 2025-11-05 23:28:01.488004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a037f8283f46'
down_revision: Union[str, None] = 'add_perf_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bus_schedules table
    op.create_table(
        'bus_schedules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('direction', sa.Enum('outbound', 'inbound', name='direction'), nullable=False),
        sa.Column('departure_time', sa.Time(), nullable=False),
        sa.Column('arrival_time', sa.Time(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('is_late_night', sa.Boolean(), server_default='false', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('idx_bus_direction_dow', 'bus_schedules', ['direction', 'day_of_week'])
    op.create_index('idx_bus_departure_time', 'bus_schedules', ['departure_time'])

    # Create user_bus_preferences table
    op.create_table(
        'user_bus_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('auto_create_events', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('arrival_buffer_minutes', sa.Integer(), server_default='15', nullable=True),
        sa.Column('departure_buffer_minutes', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create index on user_id for faster lookups
    op.create_index('idx_user_bus_prefs_user_id', 'user_bus_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_user_bus_prefs_user_id', table_name='user_bus_preferences')
    op.drop_index('idx_bus_departure_time', table_name='bus_schedules')
    op.drop_index('idx_bus_direction_dow', table_name='bus_schedules')

    # Drop tables
    op.drop_table('user_bus_preferences')
    op.drop_table('bus_schedules')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS direction")
