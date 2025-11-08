"""add_assignment_type_field

Revision ID: 6495171d457e
Revises: ae4f57de6a6d
Create Date: 2025-11-07 19:37:48.383913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6495171d457e'
down_revision: Union[str, None] = 'ae4f57de6a6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add assignment_type column to assignments table
    op.add_column('assignments', sa.Column('assignment_type', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove assignment_type column from assignments table
    op.drop_column('assignments', 'assignment_type')
