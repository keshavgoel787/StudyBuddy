"""
Service for building day context summaries for the planning agent.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from app.schemas.calendar import CalendarEvent
from app.models.assignment import Assignment


@dataclass
class DayContext:
    """Summary of a day's schedule for planning decisions."""
    date: date
    total_awake_hours: float
    total_busy_hours: float
    total_study_hours_if_applied: float
    free_hours_if_applied: float
    has_exam_within_2_days: bool
    days_until_next_exam: Optional[int]
    assignments_summary: List[dict]  # {id, title, due_in_days, estimated_hours}


def build_day_context(
    today: date,
    events: List[CalendarEvent],
    candidate_blocks: List[CalendarEvent],
    assignments: List[Assignment],
    exams: List[CalendarEvent] = None,
    day_start_hour: int = 8,
    day_end_hour: int = 23,
) -> DayContext:
    """
    Build a comprehensive day context for the planning agent.

    Args:
        today: The date being analyzed
        events: Existing calendar events (classes, commute, etc)
        candidate_blocks: Proposed assignment study blocks
        assignments: List of user's assignments
        exams: List of exam events (optional, can extract from events)
        day_start_hour: When the day starts (default 8 AM)
        day_end_hour: When the day ends (default 11 PM)

    Returns:
        DayContext with all metrics calculated
    """
    if exams is None:
        exams = []

    # Calculate total awake hours
    total_awake_hours = day_end_hour - day_start_hour

    # Calculate busy hours (all events including proposed assignments)
    all_events = events + candidate_blocks
    total_busy_hours = sum(
        (e.end - e.start).total_seconds() / 3600
        for e in all_events
    )

    # Calculate study hours (existing + candidate assignment blocks)
    existing_study_hours = sum(
        (e.end - e.start).total_seconds() / 3600
        for e in events
        if hasattr(e, 'event_type') and e.event_type == "assignment"
    )
    candidate_study_hours = sum(
        (e.end - e.start).total_seconds() / 3600
        for e in candidate_blocks
    )
    total_study_hours_if_applied = existing_study_hours + candidate_study_hours

    # Calculate free hours if we apply candidate blocks
    free_hours_if_applied = total_awake_hours - total_busy_hours

    # Exam detection
    # Strategy 1: Check provided exams list
    # Strategy 2: Look for events with "exam" or "test" in title
    exam_events = exams if exams else []
    if not exam_events:
        exam_keywords = ["exam", "test", "quiz", "midterm", "final"]
        exam_events = [
            e for e in events
            if any(keyword in e.title.lower() for keyword in exam_keywords)
        ]

    # Find next exam
    has_exam_within_2_days = False
    days_until_next_exam = None

    if exam_events:
        # Sort exams by start time
        future_exams = [
            e for e in exam_events
            if e.start.date() >= today
        ]
        future_exams.sort(key=lambda e: e.start)

        if future_exams:
            next_exam = future_exams[0]
            days_until = (next_exam.start.date() - today).days

            days_until_next_exam = days_until
            has_exam_within_2_days = days_until <= 2

    # Build assignments summary
    assignments_summary = []
    for assignment in assignments:
        due_in_days = (assignment.due_date.date() - today).days
        assignments_summary.append({
            "id": assignment.id,
            "title": assignment.title,
            "due_in_days": due_in_days,
            "estimated_hours": assignment.estimated_hours,
            "priority": assignment.priority,
        })

    # Sort by due date
    assignments_summary.sort(key=lambda a: a["due_in_days"])

    return DayContext(
        date=today,
        total_awake_hours=total_awake_hours,
        total_busy_hours=total_busy_hours,
        total_study_hours_if_applied=total_study_hours_if_applied,
        free_hours_if_applied=free_hours_if_applied,
        has_exam_within_2_days=has_exam_within_2_days,
        days_until_next_exam=days_until_next_exam,
        assignments_summary=assignments_summary,
    )
