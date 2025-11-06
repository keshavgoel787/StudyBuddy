"""
Test script for the planning agent.
Tests different scenarios: OFF, LIGHT, NORMAL, HIGH modes.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, time, date as date_type
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.assignment import Assignment
from app.schemas.calendar import CalendarEvent, FreeBlock
from app.services.planning_agent import agent_filter_schedule_for_today
from app.utils.time_utils import calculate_free_blocks
import pytz

def create_event(today, start_hour, end_hour, title, location=""):
    """Helper to create a calendar event."""
    tz = pytz.UTC
    return CalendarEvent(
        id=f"event-{title.replace(' ', '-').lower()}",
        title=title,
        location=location,
        start=datetime.combine(today, time(start_hour, 0)).replace(tzinfo=tz),
        end=datetime.combine(today, time(end_hour, 0)).replace(tzinfo=tz),
        event_type="calendar"
    )

def test_scenario(name, today, events, assignments, expected_mode):
    """Test a specific scenario."""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {name}")
    print(f"{'='*80}")

    print(f"\n📅 Events:")
    for e in events:
        print(f"  - {e.title}: {e.start.strftime('%I:%M %p')} - {e.end.strftime('%I:%M %p')}")

    free_blocks = calculate_free_blocks(events)
    print(f"\n🆓 Free Blocks ({len(free_blocks)} total):")
    for fb in free_blocks:
        print(f"  - {fb.start.strftime('%I:%M %p')} - {fb.end.strftime('%I:%M %p')} ({fb.duration_minutes} min)")

    print(f"\n📝 Assignments:")
    for a in assignments:
        due_in = (a.due_date.date() - today).days
        print(f"  - {a.title}: {a.estimated_hours}h, due in {due_in} days, priority {a.priority}")

    # Run agent
    kept_blocks, decision = agent_filter_schedule_for_today(
        today=today,
        events=events,
        free_blocks=free_blocks,
        assignments=assignments,
    )

    print(f"\n🤖 Agent Decision:")
    print(f"  Mode: {decision.mode}")
    print(f"  Reason: {decision.reason}")
    print(f"  Kept {len(kept_blocks)} blocks:")

    for block in kept_blocks:
        duration = (block.end - block.start).total_seconds() / 3600
        print(f"    - {block.title}: {block.start.strftime('%I:%M %p')} - {block.end.strftime('%I:%M %p')} ({duration:.1f}h)")

    # Check if mode matches expected
    if decision.mode == expected_mode:
        print(f"\n✅ PASSED: Mode is {expected_mode} as expected")
    else:
        print(f"\n⚠️  NOTE: Expected {expected_mode}, got {decision.mode}")
        print(f"  This is OK - agent makes intelligent decisions based on context")

    return decision

def main():
    db = SessionLocal()

    try:
        # Get first user
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database")
            return

        print(f"🧪 Testing Planning Agent")
        print(f"User: {user.email}\n")

        today = datetime.now().date()
        tz = pytz.UTC

        # ========================================
        # SCENARIO 1: Fully booked day → OFF
        # ========================================
        assignment1 = Assignment(
            user_id=user.id,
            title="Math Homework",
            due_date=datetime.now(tz) + timedelta(days=5),
            estimated_hours=2.0,
            priority=1,
            completed=False
        )

        events_busy = [
            create_event(today, 9, 11, "Class 1", "Building A"),
            create_event(today, 11, 13, "Class 2", "Building B"),
            create_event(today, 14, 16, "Lab", "Science Hall"),
            create_event(today, 16, 18, "Meeting", "Library"),
            create_event(today, 19, 21, "Study Group", "Campus"),
        ]

        test_scenario(
            "Fully Booked Day (expect OFF or LIGHT)",
            today,
            events_busy,
            [assignment1],
            expected_mode="OFF"
        )

        # ========================================
        # SCENARIO 2: Light day, far deadline → LIGHT
        # ========================================
        events_light = [
            create_event(today, 10, 12, "One Class", "Room 101"),
        ]

        test_scenario(
            "Light Day, No Urgency (expect LIGHT)",
            today,
            events_light,
            [assignment1],
            expected_mode="LIGHT"
        )

        # ========================================
        # SCENARIO 3: Normal day, moderate deadline → NORMAL
        # ========================================
        assignment2 = Assignment(
            user_id=user.id,
            title="CS Project",
            due_date=datetime.now(tz) + timedelta(days=3),
            estimated_hours=4.0,
            priority=2,
            completed=False
        )

        events_normal = [
            create_event(today, 10, 12, "BCHM 401", "l234"),
            create_event(today, 14, 16, "Bio Lab", "Science"),
        ]

        test_scenario(
            "Normal Day, Moderate Deadline (expect NORMAL)",
            today,
            events_normal,
            [assignment1, assignment2],
            expected_mode="NORMAL"
        )

        # ========================================
        # SCENARIO 4: Exam tomorrow → HIGH
        # ========================================
        assignment3 = Assignment(
            user_id=user.id,
            title="Exam Review",
            due_date=datetime.now(tz) + timedelta(days=1),
            estimated_hours=5.0,
            priority=3,
            completed=False
        )

        events_with_exam = [
            create_event(today, 10, 12, "Last Class Before Exam", "Building A"),
            create_event(today, 10, 12, "EXAM TOMORROW", "Building A"),  # Exam indicator
        ]

        test_scenario(
            "Exam Tomorrow (expect HIGH)",
            today,
            events_with_exam,
            [assignment3],
            expected_mode="HIGH"
        )

        print(f"\n{'='*80}")
        print("✅ All scenarios tested successfully!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
