"""add performance indexes

Revision ID: add_perf_indexes
Revises: 1993c7d3f42e
Create Date: 2025-11-05

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'add_perf_indexes'
down_revision = '1993c7d3f42e'  # Points to add_day_plans_table_for_caching
branch_labels = None
depends_on = None


def upgrade():
    # Note: Some indexes may already exist from SQLAlchemy auto-creation
    # Using CREATE INDEX IF NOT EXISTS pattern

    # Create indexes with conditional creation (PostgreSQL-specific)
    from sqlalchemy import text
    conn = op.get_bind()

    # Add index on note_documents.user_id for faster filtering
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_note_documents_user_id ON note_documents (user_id)"
    ))

    # Add composite index on day_plans for date-based lookups by user
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_day_plans_user_date ON day_plans (user_id, date)"
    ))

    # Add index on study_material.note_document_id for faster joins
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_study_material_note_document_id ON study_material (note_document_id)"
    ))

    # Add index on user_tokens.user_id for faster token lookups
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_user_tokens_user_id ON user_tokens (user_id)"
    ))


def downgrade():
    # Only drop if exists
    from sqlalchemy import text
    conn = op.get_bind()

    conn.execute(text("DROP INDEX IF EXISTS ix_user_tokens_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_study_material_note_document_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_day_plans_user_date"))
    conn.execute(text("DROP INDEX IF EXISTS ix_note_documents_user_id"))
