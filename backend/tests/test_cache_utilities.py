"""
Tests for cache utility functions.
"""

import pytest
from datetime import date, timedelta

from app.utils.cache import invalidate_day_plan_cache, cleanup_old_day_plans
from app.models.day_plan import DayPlan


class TestInvalidateDayPlanCache:
    """Test suite for invalidate_day_plan_cache function."""

    def test_invalidate_existing_cache(self, db_session, test_user):
        """Test invalidating an existing cached day plan."""
        today = date.today()

        # Create cached plan
        cached_plan = DayPlan(
            user_id=test_user.id,
            date=today,
            events=[],
            free_blocks=[],
            recommendations={
                "lunch_slots": [],
                "study_slots": [],
                "commute_suggestion": None,
                "summary": "Test plan"
            }
        )
        db_session.add(cached_plan)
        db_session.commit()

        # Invalidate cache
        deleted = invalidate_day_plan_cache(db_session, test_user.id, today)

        assert deleted == 1

        # Verify cache is gone
        remaining = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id,
            DayPlan.date == today
        ).first()

        assert remaining is None

    def test_invalidate_nonexistent_cache(self, db_session, test_user):
        """Test invalidating cache that doesn't exist."""
        today = date.today()

        # No cached plan exists
        deleted = invalidate_day_plan_cache(db_session, test_user.id, today)

        assert deleted == 0

    def test_invalidate_specific_date(self, db_session, test_user):
        """Test invalidating cache for specific date."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Create plans for today and tomorrow
        plan_today = DayPlan(
            user_id=test_user.id,
            date=today,
            events=[],
            free_blocks=[],
            recommendations={"summary": "Today"}
        )
        plan_tomorrow = DayPlan(
            user_id=test_user.id,
            date=tomorrow,
            events=[],
            free_blocks=[],
            recommendations={"summary": "Tomorrow"}
        )
        db_session.add(plan_today)
        db_session.add(plan_tomorrow)
        db_session.commit()

        # Invalidate only today
        deleted = invalidate_day_plan_cache(db_session, test_user.id, today)

        assert deleted == 1

        # Verify only today's plan is gone
        remaining_today = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id,
            DayPlan.date == today
        ).first()
        remaining_tomorrow = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id,
            DayPlan.date == tomorrow
        ).first()

        assert remaining_today is None
        assert remaining_tomorrow is not None

    def test_invalidate_defaults_to_today(self, db_session, test_user):
        """Test that invalidate defaults to today's date."""
        today = date.today()

        # Create plan for today
        cached_plan = DayPlan(
            user_id=test_user.id,
            date=today,
            events=[],
            free_blocks=[],
            recommendations={"summary": "Test"}
        )
        db_session.add(cached_plan)
        db_session.commit()

        # Invalidate without specifying date
        deleted = invalidate_day_plan_cache(db_session, test_user.id)

        assert deleted == 1

    def test_invalidate_only_affects_specific_user(self, db_session, test_user):
        """Test that invalidation only affects specified user."""
        from app.models.user import User

        # Create another user
        other_user = User(
            google_id="other_user_123",
            email="other@example.com",
            name="Other User"
        )
        db_session.add(other_user)
        db_session.commit()

        today = date.today()

        # Create plans for both users
        plan1 = DayPlan(
            user_id=test_user.id,
            date=today,
            events=[],
            free_blocks=[],
            recommendations={"summary": "User 1"}
        )
        plan2 = DayPlan(
            user_id=other_user.id,
            date=today,
            events=[],
            free_blocks=[],
            recommendations={"summary": "User 2"}
        )
        db_session.add(plan1)
        db_session.add(plan2)
        db_session.commit()

        # Invalidate only test_user's cache
        deleted = invalidate_day_plan_cache(db_session, test_user.id, today)

        assert deleted == 1

        # Verify only test_user's plan is gone
        remaining_user1 = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id,
            DayPlan.date == today
        ).first()
        remaining_user2 = db_session.query(DayPlan).filter(
            DayPlan.user_id == other_user.id,
            DayPlan.date == today
        ).first()

        assert remaining_user1 is None
        assert remaining_user2 is not None


class TestCleanupOldDayPlans:
    """Test suite for cleanup_old_day_plans function."""

    def test_cleanup_old_plans(self, db_session, test_user):
        """Test cleaning up old day plans."""
        today = date.today()

        # Create plans: 1 recent, 2 old
        recent_plan = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=3),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Recent"}
        )
        old_plan1 = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=10),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Old 1"}
        )
        old_plan2 = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=15),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Old 2"}
        )
        db_session.add(recent_plan)
        db_session.add(old_plan1)
        db_session.add(old_plan2)
        db_session.commit()

        # Cleanup plans older than 7 days
        deleted = cleanup_old_day_plans(db_session, days_to_keep=7)

        assert deleted == 2

        # Verify only recent plan remains
        remaining = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id
        ).all()

        assert len(remaining) == 1
        assert remaining[0].date == today - timedelta(days=3)

    def test_cleanup_no_old_plans(self, db_session, test_user):
        """Test cleanup when no old plans exist."""
        today = date.today()

        # Create only recent plans
        recent_plan = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=2),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Recent"}
        )
        db_session.add(recent_plan)
        db_session.commit()

        # Cleanup
        deleted = cleanup_old_day_plans(db_session, days_to_keep=7)

        assert deleted == 0

        # Verify plan still exists
        remaining = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id
        ).first()

        assert remaining is not None

    def test_cleanup_custom_retention(self, db_session, test_user):
        """Test cleanup with custom retention period."""
        today = date.today()

        # Create plans at various ages
        plans = [
            DayPlan(
                user_id=test_user.id,
                date=today - timedelta(days=days),
                events=[],
                free_blocks=[],
                recommendations={"summary": f"Plan {days} days ago"}
            )
            for days in [1, 5, 10, 15, 20]
        ]
        for plan in plans:
            db_session.add(plan)
        db_session.commit()

        # Keep only last 14 days
        deleted = cleanup_old_day_plans(db_session, days_to_keep=14)

        # Should delete 2 plans (15 and 20 days old)
        assert deleted == 2

        # Verify 3 plans remain (1, 5, 10 days old)
        remaining = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id
        ).all()

        assert len(remaining) == 3

    def test_cleanup_affects_all_users(self, db_session, test_user):
        """Test that cleanup affects all users' old plans."""
        from app.models.user import User

        # Create another user
        other_user = User(
            google_id="other_user_456",
            email="other@example.com",
            name="Other User"
        )
        db_session.add(other_user)
        db_session.commit()

        today = date.today()

        # Create old plans for both users
        old_plan1 = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=10),
            events=[],
            free_blocks=[],
            recommendations={"summary": "User 1 old"}
        )
        old_plan2 = DayPlan(
            user_id=other_user.id,
            date=today - timedelta(days=10),
            events=[],
            free_blocks=[],
            recommendations={"summary": "User 2 old"}
        )
        db_session.add(old_plan1)
        db_session.add(old_plan2)
        db_session.commit()

        # Cleanup
        deleted = cleanup_old_day_plans(db_session, days_to_keep=7)

        # Should delete both users' old plans
        assert deleted == 2

    def test_cleanup_boundary_case(self, db_session, test_user):
        """Test cleanup on exact boundary date."""
        today = date.today()

        # Create plan exactly 7 days old
        boundary_plan = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=7),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Boundary"}
        )
        db_session.add(boundary_plan)
        db_session.commit()

        # Cleanup with 7 days retention
        deleted = cleanup_old_day_plans(db_session, days_to_keep=7)

        # Plan exactly 7 days old should NOT be deleted (< cutoff, not <=)
        assert deleted == 0

        remaining = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id
        ).first()

        assert remaining is not None

    def test_cleanup_empty_database(self, db_session):
        """Test cleanup with no plans in database."""
        deleted = cleanup_old_day_plans(db_session, days_to_keep=7)

        assert deleted == 0

    def test_cleanup_preserves_today_and_future(self, db_session, test_user):
        """Test that cleanup preserves today and future plans."""
        today = date.today()

        # Create plans: old, today, future
        old_plan = DayPlan(
            user_id=test_user.id,
            date=today - timedelta(days=10),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Old"}
        )
        today_plan = DayPlan(
            user_id=test_user.id,
            date=today,
            events=[],
            free_blocks=[],
            recommendations={"summary": "Today"}
        )
        future_plan = DayPlan(
            user_id=test_user.id,
            date=today + timedelta(days=5),
            events=[],
            free_blocks=[],
            recommendations={"summary": "Future"}
        )
        db_session.add(old_plan)
        db_session.add(today_plan)
        db_session.add(future_plan)
        db_session.commit()

        # Cleanup
        deleted = cleanup_old_day_plans(db_session, days_to_keep=7)

        # Only old plan should be deleted
        assert deleted == 1

        # Verify today and future plans remain
        remaining = db_session.query(DayPlan).filter(
            DayPlan.user_id == test_user.id
        ).all()

        assert len(remaining) == 2
        remaining_dates = {plan.date for plan in remaining}
        assert today in remaining_dates
        assert today + timedelta(days=5) in remaining_dates
