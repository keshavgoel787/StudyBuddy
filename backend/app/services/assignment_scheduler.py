"""
Service for scheduling assignments into the calendar.
"""

from datetime import datetime, date, time, timedelta
from typing import List
import uuid

from app.schemas.calendar import CalendarEvent, FreeBlock
from app.models.assignment import Assignment
from app.utils.logger import log_info, log_debug

# Configuration constants
DAY_START_HOUR = 8   # 08:00
DAY_END_HOUR = 23    # 23:00 / 11pm
MAX_STUDY_HOURS_PER_DAY = 4.0
DEFAULT_BLOCK_HOURS = 1.0      # length of each study block
MIN_BLOCK_MINUTES = 30         # don't create tiny 10min blocks
LOOKAHEAD_DAYS = 7             # for later multi-day logic


def propose_assignment_blocks_for_today(
    today: date,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    assignments: List[Assignment],
) -> List[CalendarEvent]:
    """
    Deterministically proposes assignment study blocks for today, but does NOT
    write anything to the DB or cache.
    All returned events have event_type="assignment" and a unique id.

    Args:
        today: The date to schedule for
        events: Existing calendar events (may include previously scheduled assignment blocks)
        free_blocks: Available free time slots
        assignments: List of user's assignments

    Returns:
        List of proposed CalendarEvent objects with event_type="assignment"
    """
    log_info("assignment_scheduler", "Starting assignment scheduling",
            date=str(today),
            free_blocks=len(free_blocks),
            total_assignments=len(assignments))

    # Step 1: Filter to incomplete assignments that are due >= today
    today_midnight = datetime.combine(today, time.min)
    if today_midnight.tzinfo is None:
        # Make timezone-aware if needed (use UTC as default)
        import pytz
        today_midnight = today_midnight.replace(tzinfo=pytz.UTC)

    eligible_assignments = [
        a for a in assignments
        if not a.completed and a.due_date >= today_midnight
    ]

    log_debug("assignment_scheduler", "Eligible assignments found",
             eligible=len(eligible_assignments))

    if not eligible_assignments:
        log_info("assignment_scheduler", "No eligible assignments to schedule")
        return []

    # Step 2: Sort assignments by due_date ascending, then priority descending
    eligible_assignments.sort(key=lambda a: (a.due_date, -a.priority))

    log_debug("assignment_scheduler", "Top 3 sorted assignments",
             assignments=[f"{a.title} (due {a.due_date}, P{a.priority}, {a.estimated_hours}h)"
                         for a in eligible_assignments[:3]])

    # Step 3: Calculate how many hours already scheduled today
    already_scheduled_hours = sum(
        (e.end - e.start).total_seconds() / 3600
        for e in events
        if hasattr(e, 'event_type') and e.event_type == "assignment"
    )

    log_debug("assignment_scheduler", "Already scheduled hours",
             hours=f"{already_scheduled_hours:.1f}h")

    # Step 4: Iterate through assignments and place blocks
    assignment_events = []
    block_counter = {}  # Track block index per assignment

    for assignment in eligible_assignments:
        # Decide how many hours to schedule for this assignment today
        hours_available_today = MAX_STUDY_HOURS_PER_DAY - already_scheduled_hours

        if hours_available_today <= 0:
            log_debug("assignment_scheduler", "Hit max study hours, stopping",
                     max_hours=MAX_STUDY_HOURS_PER_DAY)
            break

        hours_for_this_assignment_today = min(
            assignment.estimated_hours,
            hours_available_today,
            2.0,  # don't schedule more than 2h of one assignment in a single day
        )

        if hours_for_this_assignment_today <= 0:
            continue

        log_debug("assignment_scheduler", "Scheduling assignment",
                 title=assignment.title,
                 hours=f"{hours_for_this_assignment_today:.1f}h")

        # Step 5: Place study blocks into free blocks
        remaining_hours = hours_for_this_assignment_today
        block_counter[assignment.id] = 0  # Initialize counter for this assignment

        for free_block in sorted(free_blocks, key=lambda b: b.start):
            if remaining_hours <= 0:
                break

            # Calculate available duration in this free block
            free_duration_hours = free_block.duration_minutes / 60.0

            if free_duration_hours < MIN_BLOCK_MINUTES / 60.0:
                continue  # Skip tiny blocks

            # Start placing blocks within this free block
            cursor = free_block.start

            while remaining_hours > 0 and cursor < free_block.end:
                # Determine block duration
                time_until_free_end = (free_block.end - cursor).total_seconds() / 3600

                if time_until_free_end < MIN_BLOCK_MINUTES / 60.0:
                    break  # Not enough time left in this free block

                block_hours = min(
                    DEFAULT_BLOCK_HOURS,
                    remaining_hours,
                    time_until_free_end
                )

                block_start = cursor
                block_end = cursor + timedelta(hours=block_hours)

                # Ensure block doesn't go past DAY_END_HOUR
                day_end = datetime.combine(block_start.date(), time(DAY_END_HOUR, 0))
                if block_start.tzinfo:
                    day_end = day_end.replace(tzinfo=block_start.tzinfo)

                if block_end > day_end:
                    block_end = day_end
                    block_hours = (block_end - block_start).total_seconds() / 3600

                if block_hours < MIN_BLOCK_MINUTES / 60.0:
                    break  # Can't fit a meaningful block

                # Create the assignment event
                days_until_due = (assignment.due_date.date() - today).days

                assignment_event = CalendarEvent(
                    id=f"assignment-{assignment.id}-{block_counter[assignment.id]}",
                    title=f"Work on {assignment.title}",
                    start=block_start,
                    end=block_end,
                    location="",
                    description=f"Auto-scheduled study block for assignment due {assignment.due_date.isoformat()} (in {days_until_due} days)",
                    event_type="assignment"
                )
                block_counter[assignment.id] += 1

                assignment_events.append(assignment_event)

                log_debug("assignment_scheduler", "Added block",
                         time=f"{block_start.strftime('%I:%M %p')}-{block_end.strftime('%I:%M %p')}",
                         hours=f"{block_hours:.1f}h")

                # Move cursor and update counters
                cursor = block_end
                remaining_hours -= block_hours
                already_scheduled_hours += block_hours

                # Check if we've hit the daily max
                if already_scheduled_hours >= MAX_STUDY_HOURS_PER_DAY:
                    log_debug("assignment_scheduler", "Hit max hours while placing blocks")
                    break

            if already_scheduled_hours >= MAX_STUDY_HOURS_PER_DAY:
                break

    total_hours = sum((e.end - e.start).total_seconds() / 3600 for e in assignment_events)
    log_info("assignment_scheduler", "Created assignment blocks",
            blocks=len(assignment_events),
            total_hours=f"{total_hours:.1f}h")

    return assignment_events


def schedule_assignments_for_today(
    today: date,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    assignments: List[Assignment],
) -> List[CalendarEvent]:
    """
    Wrapper function for backwards compatibility.
    Calls propose_assignment_blocks_for_today and returns the result.
    """
    return propose_assignment_blocks_for_today(today, events, free_blocks, assignments)
