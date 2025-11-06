"""
Script to clear cached day plans.
Run this to force regeneration of day plans.

Usage:
    python -m scripts.clear_day_plan_cache
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.day_plan import DayPlan


def main():
    """Clear all cached day plans for today."""
    db = SessionLocal()

    try:
        today = date.today()

        # Delete today's cached plans
        deleted = db.query(DayPlan).filter(
            DayPlan.date == today
        ).delete()

        db.commit()

        print(f"✓ Cleared {deleted} cached day plan(s) for {today}")

    except Exception as e:
        print(f"✗ Error clearing cache: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
