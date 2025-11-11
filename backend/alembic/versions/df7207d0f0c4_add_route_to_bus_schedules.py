"""add_route_to_bus_schedules

Revision ID: df7207d0f0c4
Revises: a59e59417c5e
Create Date: 2025-11-11 17:56:12.057169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df7207d0f0c4'
down_revision: Union[str, None] = 'a59e59417c5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the route enum type
    route_enum = sa.Enum('westside', 'union', name='route', create_type=False)
    route_enum.create(op.get_bind(), checkfirst=True)

    # Add route column with default 'westside' for existing rows
    op.add_column('bus_schedules', sa.Column('route', route_enum, nullable=False, server_default='westside'))


def downgrade() -> None:
    # Remove the route column
    op.drop_column('bus_schedules', 'route')

    # Drop the route enum type
    sa.Enum(name='route').drop(op.get_bind(), checkfirst=True)
