"""
Test script for assignment scheduling integration.
Creates test assignments and simulates the scheduling flow.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, time
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.assignment import Assignment
from app.schemas.calendar import CalendarEvent, FreeBlock
from app.services.assignment_scheduler import schedule_assignments_for_today
from app.utils.time_utils import calculate_free_blocks
import pytz

def test_assignment_scheduling():
    db = SessionLocal()

    try:
        # Get first user for testing
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database")
            return

        print(f"✅ Testing with user: {user.email}\n")

        # Create test scenario: busy class day with one assignment
        today = datetime.now().date()
        tz = pytz.UTC

        # Scenario: Classes from 10 AM - 12 PM and 2 PM - 4 PM
        # Free blocks: 8-10 AM, 12-2 PM, 4-11 PM
        events = [
            CalendarEvent(
                id="class1",
                title="BCHM 401 - LEC",
                location="l234",
                start=datetime.combine(today, time(10, 0)).replace(tzinfo=tz),
                end=datetime.combine(today, time(12, 0)).replace(tzinfo=tz),
                event_type="calendar"
            ),
            CalendarEvent(
                id="class2",
                title="Bio Lab",
                location="Science Building",
                start=datetime.combine(today, time(14, 0)).replace(tzinfo=tz),
                end=datetime.combine(today, time(16, 0)).replace(tzinfo=tz),
                event_type="calendar"
            ),
        ]

        print("📅 Today's Calendar Events:")
        for e in events:
            print(f"  - {e.title}: {e.start.strftime('%I:%M %p')} - {e.end.strftime('%I:%M %p')}")

        # Calculate free blocks
        free_blocks = calculate_free_blocks(events)
        print(f"\n🆓 Free Blocks ({len(free_blocks)} total):")
        for fb in free_blocks:
            print(f"  - {fb.start.strftime('%I:%M %p')} - {fb.end.strftime('%I:%M %p')} ({fb.duration_minutes} min)")

        # Create test assignment
        test_assignment = Assignment(
            user_id=user.id,
            title="Chemistry Problem Set",
            description="Complete problems 1-10 from chapter 5",
            due_date=datetime.now(tz) + timedelta(days=3),
            estimated_hours=2.5,
            priority=2,
            completed=False
        )
        db.add(test_assignment)
        db.commit()
        db.refresh(test_assignment)

        print(f"\n📝 Test Assignment:")
        print(f"  - {test_assignment.title}")
        print(f"  - Due: {test_assignment.due_date.strftime('%Y-%m-%d')} (in 3 days)")
        print(f"  - Estimated: {test_assignment.estimated_hours} hours")
        print(f"  - Priority: {test_assignment.priority}")

        # Run scheduler
        print(f"\n🤖 Running Assignment Scheduler...")
        print("="*80)

        assignment_events = schedule_assignments_for_today(
            today=today,
            events=events,
            free_blocks=free_blocks,
            assignments=[test_assignment],
        )

        print("="*80)
        print(f"\n✅ Scheduler created {len(assignment_events)} assignment blocks:\n")

        total_scheduled_hours = 0
        for ae in assignment_events:
            duration = (ae.end - ae.start).total_seconds() / 3600
            total_scheduled_hours += duration
            print(f"  📚 {ae.title}")
            print(f"     Time: {ae.start.strftime('%I:%M %p')} - {ae.end.strftime('%I:%M %p')} ({duration:.1f}h)")
            print(f"     Description: {ae.description}")
            print()

        print(f"📊 Total scheduled: {total_scheduled_hours:.1f} hours")
        print(f"📊 Remaining on assignment: {test_assignment.estimated_hours - total_scheduled_hours:.1f} hours (for future days)")

        # Test merged schedule
        all_events = events + assignment_events
        all_events.sort(key=lambda e: e.start)

        print(f"\n📅 Complete Day Schedule (Calendar + Assignment Blocks):")
        for e in all_events:
            event_type_icon = "📚" if e.event_type == "assignment" else "🎓"
            print(f"  {event_type_icon} {e.start.strftime('%I:%M %p')} - {e.end.strftime('%I:%M %p')}: {e.title}")

        # Recompute free blocks after scheduling
        remaining_free = calculate_free_blocks(all_events)
        print(f"\n🆓 Remaining Free Time ({len(remaining_free)} blocks):")
        for fb in remaining_free:
            print(f"  - {fb.start.strftime('%I:%M %p')} - {fb.end.strftime('%I:%M %p')} ({fb.duration_minutes} min)")

        # Clean up test data
        db.delete(test_assignment)
        db.commit()
        print(f"\n✅ Test completed successfully! Cleaned up test assignment.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_assignment_scheduling()
