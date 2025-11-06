"""add_day_preferences_table

Revision ID: ae4f57de6a6d
Revises: e3af5cd40a0c
Create Date: 2025-11-06 15:58:07.721545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae4f57de6a6d'
down_revision: Union[str, None] = 'e3af5cd40a0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import text
    conn = op.get_bind()

    # Create enum types (if not exists)
    conn.execute(text("DO $$ BEGIN CREATE TYPE moodtype AS ENUM ('chill', 'normal', 'grind'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))
    conn.execute(text("DO $$ BEGIN CREATE TYPE feelingtype AS ENUM ('overwhelmed', 'okay', 'on_top'); EXCEPTION WHEN duplicate_object THEN null; END $$;"))

    # Create day_preferences table using raw SQL to avoid SQLAlchemy enum creation issues
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS day_preferences (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            mood moodtype NOT NULL DEFAULT 'normal',
            feeling feelingtype NOT NULL DEFAULT 'okay',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    # Create indexes
    op.create_index('ix_day_preferences_user_id', 'day_preferences', ['user_id'])
    op.create_index('ix_day_preferences_date', 'day_preferences', ['date'])
    op.create_index('ix_day_preferences_user_date', 'day_preferences', ['user_id', 'date'])


def downgrade() -> None:
    op.drop_index('ix_day_preferences_user_date', 'day_preferences')
    op.drop_index('ix_day_preferences_date', 'day_preferences')
    op.drop_index('ix_day_preferences_user_id', 'day_preferences')
    op.drop_table('day_preferences')
    op.execute('DROP TYPE feelingtype')
    op.execute('DROP TYPE moodtype')
