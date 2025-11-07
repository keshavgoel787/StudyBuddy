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
    # Using CREATE INDEX IF NOT EXISTS pattern with table existence checks

    # Create indexes with conditional creation (PostgreSQL-specific)
    from sqlalchemy import text
    conn = op.get_bind()

    # Helper function to check if table exists
    def table_exists(table_name):
        result = conn.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
        ))
        return result.scalar()

    # Add index on note_documents.user_id for faster filtering
    if table_exists('note_documents'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_note_documents_user_id ON note_documents (user_id)"
        ))

    # Add composite index on day_plans for date-based lookups by user
    if table_exists('day_plans'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_day_plans_user_date ON day_plans (user_id, date)"
        ))

    # Add index on study_material.note_document_id for faster joins
    if table_exists('study_material'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_study_material_note_document_id ON study_material (note_document_id)"
        ))

    # Add index on user_tokens.user_id for faster token lookups
    if table_exists('user_tokens'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_user_tokens_user_id ON user_tokens (user_id)"
        ))

    # Add composite index on assignments for common filtering pattern
    # Query pattern: WHERE user_id = ? AND completed = False ORDER BY due_date
    if table_exists('assignments'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_assignments_user_completed_due ON assignments (user_id, completed, due_date)"
        ))

    # Add composite index on bus_schedules for direction + day lookups
    # Query pattern: WHERE direction = ? AND day_of_week = ? AND (arrival_time/departure_time comparison)
    if table_exists('bus_schedules'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_bus_schedules_direction_day_arrival ON bus_schedules (direction, day_of_week, arrival_time)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_bus_schedules_direction_day_departure ON bus_schedules (direction, day_of_week, departure_time)"
        ))

    # Add index on user_bus_preferences.user_id for faster lookups
    if table_exists('user_bus_preferences'):
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_user_bus_preferences_user_id ON user_bus_preferences (user_id)"
        ))


def downgrade():
    # Only drop if exists
    from sqlalchemy import text
    conn = op.get_bind()

    conn.execute(text("DROP INDEX IF EXISTS ix_user_bus_preferences_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_bus_schedules_direction_day_departure"))
    conn.execute(text("DROP INDEX IF EXISTS ix_bus_schedules_direction_day_arrival"))
    conn.execute(text("DROP INDEX IF EXISTS ix_assignments_user_completed_due"))
    conn.execute(text("DROP INDEX IF EXISTS ix_user_tokens_user_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_study_material_note_document_id"))
    conn.execute(text("DROP INDEX IF EXISTS ix_day_plans_user_date"))
    conn.execute(text("DROP INDEX IF EXISTS ix_note_documents_user_id"))
