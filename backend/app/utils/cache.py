"""
Cache utilities for invalidating cached data.
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.day_plan import DayPlan
from app.utils.logger import log_info


def invalidate_day_plan_cache(db: Session, user_id: UUID, target_date: date = None):
    """
    Invalidate cached day plan for a specific user and date.

    Args:
        db: Database session
        user_id: User UUID
        target_date: Date to invalidate (defaults to today)
    """
    if target_date is None:
        target_date = date.today()

    deleted = db.query(DayPlan).filter(
        DayPlan.user_id == user_id,
        DayPlan.date == target_date
    ).delete()

    if deleted > 0:
        log_info("cache", "Invalidated day plan cache",
                user_id=str(user_id),
                date=str(target_date),
                deleted=deleted)

    return deleted


def cleanup_old_day_plans(db: Session, days_to_keep: int = 7):
    """
    Remove day plans older than specified days to prevent database bloat.

    Args:
        db: Database session
        days_to_keep: Number of days to keep (default: 7)

    Returns:
        Number of records deleted
    """
    cutoff_date = date.today() - timedelta(days=days_to_keep)

    deleted = db.query(DayPlan).filter(
        DayPlan.date < cutoff_date
    ).delete()

    if deleted > 0:
        log_info("cache", "Cleaned up old day plans",
                cutoff_date=str(cutoff_date),
                deleted=deleted)

    return deleted
