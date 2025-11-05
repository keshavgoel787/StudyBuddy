from datetime import datetime, time, timedelta
from typing import List
from app.schemas.calendar import CalendarEvent, FreeBlock


def calculate_free_blocks(
    events: List[CalendarEvent],
    day_start: time = time(8, 0),
    day_end: time = time(22, 0)
) -> List[FreeBlock]:
    """
    Calculate free time blocks between events.
    Assumes all events are on the same day.
    """
    if not events:
        # If no events, entire day is free
        date = datetime.now().date()
        start_dt = datetime.combine(date, day_start)
        end_dt = datetime.combine(date, day_end)
        duration = int((end_dt - start_dt).total_seconds() / 60)
        return [FreeBlock(start=start_dt, end=end_dt, duration_minutes=duration)]

    # Sort events by start time
    sorted_events = sorted(events, key=lambda e: e.start)
    date = sorted_events[0].start.date()

    free_blocks = []
    day_start_dt = datetime.combine(date, day_start)
    day_end_dt = datetime.combine(date, day_end)

    # Check for free time before first event
    if sorted_events[0].start > day_start_dt:
        duration = int((sorted_events[0].start - day_start_dt).total_seconds() / 60)
        if duration >= 15:  # Only include blocks >= 15 minutes
            free_blocks.append(FreeBlock(
                start=day_start_dt,
                end=sorted_events[0].start,
                duration_minutes=duration
            ))

    # Check for free time between events
    for i in range(len(sorted_events) - 1):
        current_end = sorted_events[i].end
        next_start = sorted_events[i + 1].start

        if next_start > current_end:
            duration = int((next_start - current_end).total_seconds() / 60)
            if duration >= 15:  # Only include blocks >= 15 minutes
                free_blocks.append(FreeBlock(
                    start=current_end,
                    end=next_start,
                    duration_minutes=duration
                ))

    # Check for free time after last event
    if sorted_events[-1].end < day_end_dt:
        duration = int((day_end_dt - sorted_events[-1].end).total_seconds() / 60)
        if duration >= 15:  # Only include blocks >= 15 minutes
            free_blocks.append(FreeBlock(
                start=sorted_events[-1].end,
                end=day_end_dt,
                duration_minutes=duration
            ))

    return free_blocks


def format_time_slot(start: datetime, end: datetime) -> str:
    """Format a time slot as 'HH:MM AM/PM - HH:MM AM/PM'"""
    return f"{start.strftime('%-I:%M %p')} - {end.strftime('%-I:%M %p')}"
