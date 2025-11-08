"""make_estimated_hours_nullable

Revision ID: a59e59417c5e
Revises: 6495171d457e
Create Date: 2025-11-07 19:53:49.800856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a59e59417c5e'
down_revision: Union[str, None] = '6495171d457e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make estimated_hours nullable in assignments table
    op.alter_column('assignments', 'estimated_hours',
                    existing_type=sa.Float(),
                    nullable=True,
                    existing_nullable=False)


def downgrade() -> None:
    # Revert estimated_hours to non-nullable (set default for null values first)
    op.execute('UPDATE assignments SET estimated_hours = 1.0 WHERE estimated_hours IS NULL')
    op.alter_column('assignments', 'estimated_hours',
                    existing_type=sa.Float(),
                    nullable=False,
                    existing_nullable=True)
