"""
Tests for assignment scheduler service.
"""

import pytest
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from app.services.assignment_scheduler import (
    propose_assignment_blocks_for_today,
    schedule_assignments_for_today,
    MAX_STUDY_HOURS_PER_DAY,
    DEFAULT_BLOCK_HOURS
)
from app.schemas.calendar import CalendarEvent, FreeBlock
from app.models.assignment import Assignment


@pytest.fixture
def est():
    """EST timezone for testing."""
    return ZoneInfo("America/New_York")


@pytest.fixture
def today_est(est):
    """Today in EST."""
    return datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)


class TestProposeAssignmentBlocks:
    """Test suite for propose_assignment_blocks_for_today function."""

    def test_no_assignments(self, est, today_est):
        """Test scheduling with no assignments."""
        today = date.today()
        free_blocks = [
            FreeBlock(
                id="free-1",
                start=today_est.replace(hour=10),
                end=today_est.replace(hour=12),
                start_label="10:00 AM",
                end_label="12:00 PM",
                duration_hours=2.0,
                duration_minutes=120,
                block_type="free"
            )
        ]

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=free_blocks,
            assignments=[]
        )

        assert len(blocks) == 0

    def test_no_free_time(self, est, today_est, test_user):
        """Test scheduling with no free time."""
        today = date.today()
        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=2),
            estimated_hours=2.0,
            priority=3,
            completed=False
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[],  # No free time
            assignments=[assignment]
        )

        assert len(blocks) == 0

    def test_single_assignment_single_block(self, est, today_est, test_user):
        """Test scheduling a single assignment into one free block."""
        today = date.today()
        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=2),
            estimated_hours=1.0,
            priority=3,
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=12),
            start_label="10:00 AM",
            end_label="12:00 PM",
            duration_hours=2.0,
            duration_minutes=120,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        assert len(blocks) == 1
        assert blocks[0].title == "Work on Physics Homework"
        assert blocks[0].event_type == "assignment"
        assert blocks[0].id == "assignment-1-0"

        # Verify block is 1 hour (default or assignment estimate, whichever is smaller)
        duration_hours = (blocks[0].end - blocks[0].start).total_seconds() / 3600
        assert duration_hours == 1.0

    def test_multiple_assignments_priority_order(self, est, today_est, test_user):
        """Test that assignments are scheduled by due date and priority."""
        today = date.today()

        # Create assignments with different due dates and priorities
        assignment1 = Assignment(
            id=1,
            user_id=test_user.id,
            title="Low Priority Task",
            due_date=today_est + timedelta(days=5),
            estimated_hours=1.0,
            priority=1,  # Low priority
            completed=False
        )

        assignment2 = Assignment(
            id=2,
            user_id=test_user.id,
            title="Urgent Task",
            due_date=today_est + timedelta(days=2),
            estimated_hours=1.0,
            priority=3,  # High priority
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=14),
            start_label="10:00 AM",
            end_label="2:00 PM",
            duration_hours=4.0,
            duration_minutes=240,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment1, assignment2]
        )

        # Urgent task (due sooner) should be scheduled first
        assert len(blocks) >= 1
        assert "Urgent Task" in blocks[0].title

    def test_max_study_hours_per_day(self, est, today_est, test_user):
        """Test that scheduler respects MAX_STUDY_HOURS_PER_DAY limit."""
        today = date.today()

        # Create assignment requiring many hours
        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Large Project",
            due_date=today_est + timedelta(days=7),
            estimated_hours=10.0,  # More than max
            priority=3,
            completed=False
        )

        # Large free block
        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=9),
            end=today_est.replace(hour=20),
            start_label="9:00 AM",
            end_label="8:00 PM",
            duration_hours=11.0,
            duration_minutes=660,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        # Calculate total scheduled hours
        total_hours = sum((b.end - b.start).total_seconds() / 3600 for b in blocks)

        # Should not exceed MAX_STUDY_HOURS_PER_DAY (4 hours)
        assert total_hours <= MAX_STUDY_HOURS_PER_DAY

    def test_max_2_hours_per_assignment_per_day(self, est, today_est, test_user):
        """Test that scheduler doesn't schedule more than 2h per assignment per day."""
        today = date.today()

        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Long Assignment",
            due_date=today_est + timedelta(days=2),
            estimated_hours=5.0,
            priority=3,
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=9),
            end=today_est.replace(hour=20),
            start_label="9:00 AM",
            end_label="8:00 PM",
            duration_hours=11.0,
            duration_minutes=660,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        # Calculate total hours for this assignment
        assignment_hours = sum((b.end - b.start).total_seconds() / 3600 for b in blocks)

        # Should not exceed 2 hours for a single assignment
        assert assignment_hours <= 2.0

    def test_stable_block_ids(self, est, today_est, test_user):
        """Test that block IDs are stable (counter-based, not random)."""
        today = date.today()

        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=2),
            estimated_hours=2.0,
            priority=3,
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=14),
            start_label="10:00 AM",
            end_label="2:00 PM",
            duration_hours=4.0,
            duration_minutes=240,
            block_type="free"
        )

        # Run twice with same inputs
        blocks1 = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        blocks2 = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        # IDs should be identical
        assert [b.id for b in blocks1] == [b.id for b in blocks2]

        # IDs should follow pattern assignment-{id}-{index}
        assert all(b.id.startswith("assignment-1-") for b in blocks1)

    def test_completed_assignments_excluded(self, est, today_est, test_user):
        """Test that completed assignments are not scheduled."""
        today = date.today()

        completed_assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Completed Task",
            due_date=today_est + timedelta(days=2),
            estimated_hours=2.0,
            priority=3,
            completed=True  # Completed
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=12),
            start_label="10:00 AM",
            end_label="12:00 PM",
            duration_hours=2.0,
            duration_minutes=120,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[completed_assignment]
        )

        assert len(blocks) == 0

    def test_past_due_assignments_excluded(self, est, today_est, test_user):
        """Test that past-due assignments are not scheduled."""
        today = date.today()

        past_assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Overdue Task",
            due_date=today_est - timedelta(days=2),  # Past due
            estimated_hours=2.0,
            priority=3,
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=12),
            start_label="10:00 AM",
            end_label="12:00 PM",
            duration_hours=2.0,
            duration_minutes=120,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[past_assignment]
        )

        assert len(blocks) == 0

    def test_multiple_free_blocks(self, est, today_est, test_user):
        """Test scheduling across multiple free blocks."""
        today = date.today()

        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=2),
            estimated_hours=3.0,
            priority=3,
            completed=False
        )

        free_blocks = [
            FreeBlock(
                id="free-1",
                start=today_est.replace(hour=10),
                end=today_est.replace(hour=11),
                start_label="10:00 AM",
                end_label="11:00 AM",
                duration_hours=1.0,
                duration_minutes=60,
                block_type="free"
            ),
            FreeBlock(
                id="free-2",
                start=today_est.replace(hour=14),
                end=today_est.replace(hour=16),
                start_label="2:00 PM",
                end_label="4:00 PM",
                duration_hours=2.0,
                duration_minutes=120,
                block_type="free"
            )
        ]

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=free_blocks,
            assignments=[assignment]
        )

        # Should create blocks in both free time slots
        assert len(blocks) >= 2

        # Verify blocks are in different time slots
        start_times = {b.start.hour for b in blocks}
        assert len(start_times) >= 2

    def test_already_scheduled_hours_counted(self, est, today_est, test_user):
        """Test that already scheduled assignment blocks are counted."""
        today = date.today()

        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=2),
            estimated_hours=4.0,
            priority=3,
            completed=False
        )

        # Already have 3 hours scheduled
        existing_events = [
            CalendarEvent(
                id="existing-1",
                title="Already Scheduled",
                start=today_est.replace(hour=9),
                end=today_est.replace(hour=12),
                event_type="assignment"
            )
        ]

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=14),
            end=today_est.replace(hour=18),
            start_label="2:00 PM",
            end_label="6:00 PM",
            duration_hours=4.0,
            duration_minutes=240,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=existing_events,
            free_blocks=[free_block],
            assignments=[assignment]
        )

        # Calculate total new hours
        new_hours = sum((b.end - b.start).total_seconds() / 3600 for b in blocks)

        # Should only add 1 more hour (max is 4, already have 3)
        assert new_hours <= 1.0

    def test_block_description_includes_due_date(self, est, today_est, test_user):
        """Test that block description includes due date information."""
        today = date.today()

        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=3),
            estimated_hours=1.0,
            priority=3,
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=12),
            start_label="10:00 AM",
            end_label="12:00 PM",
            duration_hours=2.0,
            duration_minutes=120,
            block_type="free"
        )

        blocks = propose_assignment_blocks_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        assert len(blocks) == 1
        assert "in 3 days" in blocks[0].description
        assert "due" in blocks[0].description.lower()


class TestScheduleAssignmentsForToday:
    """Test suite for schedule_assignments_for_today wrapper function."""

    def test_wrapper_function(self, est, today_est, test_user):
        """Test that wrapper function calls propose_assignment_blocks_for_today."""
        today = date.today()

        assignment = Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today_est + timedelta(days=2),
            estimated_hours=1.0,
            priority=3,
            completed=False
        )

        free_block = FreeBlock(
            id="free-1",
            start=today_est.replace(hour=10),
            end=today_est.replace(hour=12),
            start_label="10:00 AM",
            end_label="12:00 PM",
            duration_hours=2.0,
            duration_minutes=120,
            block_type="free"
        )

        blocks = schedule_assignments_for_today(
            today=today,
            events=[],
            free_blocks=[free_block],
            assignments=[assignment]
        )

        assert len(blocks) == 1
        assert blocks[0].title == "Work on Physics Homework"
