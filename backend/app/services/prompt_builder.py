"""
Optimized prompt builders for Gemini AI.
Separates prompt logic from service logic for better maintainability.
"""

from typing import List
from datetime import datetime
import re

from app.schemas.calendar import CalendarEvent, FreeBlock


def build_day_plan_prompt(
    date: str,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    morning_bus_time: str = None,
    evening_bus_time: str = None,
    planning_mode: str = None,
    planning_reason: str = None
) -> str:
    """Build optimized prompt for day plan generation."""

    # Partition events efficiently
    assignment_events = [e for e in events if getattr(e, 'event_type', 'calendar') == "assignment"]
    calendar_events = [e for e in events if getattr(e, 'event_type', 'calendar') == "calendar"]

    # Compact event formatting
    def format_time_range(start: datetime, end: datetime) -> str:
        return f"{start.strftime('%I:%M%p')}-{end.strftime('%I:%M%p')}"

    calendar_list = [f"{e.title} {format_time_range(e.start, e.end)}" for e in calendar_events]

    assignment_list = []
    for e in assignment_events:
        due_info = ""
        if hasattr(e, 'description') and e.description:
            if match := re.search(r'in (\d+) days', e.description):
                due_info = f" (due {match.group(1)}d)"
        assignment_list.append(f"{e.title} {format_time_range(e.start, e.end)}{due_info}")

    free_list = [f"{format_time_range(fb.start, fb.end)} ({fb.duration_minutes}min)" for fb in free_blocks]

    # Build compact prompt
    prompt_parts = [
        f"Day planner for pre-med student ({date})",
        "",
        f"**Classes:** {', '.join(calendar_list) if calendar_list else 'None'}",
    ]

    if assignment_list:
        prompt_parts.append(f"**Scheduled Study:** {', '.join(assignment_list)}")

    prompt_parts.append(f"**Free Time:** {', '.join(free_list) if free_list else 'None'}")

    if morning_bus_time or evening_bus_time:
        bus_times = []
        if morning_bus_time:
            bus_times.append(f"To campus: {morning_bus_time}")
        if evening_bus_time:
            bus_times.append(f"From campus: {evening_bus_time}")
        prompt_parts.append(f"**Bus:** {' | '.join(bus_times)}")

    if planning_mode and planning_reason:
        prompt_parts.append(f"**Planning Mode:** {planning_mode} - {planning_reason}")

    prompt_parts.extend([
        "",
        "Generate:",
        "1. Lunch windows (11AM-2PM, 30-60min)",
        "2. Extra study slots (ONLY if free time available)",
        "3. Commute timing",
        "4. Warm summary highlighting assigned study blocks & bus times",
        "",
        "JSON format:",
        "{",
        '  "lunch_slots": [{"start": "2025-11-08T12:00:00", "end": "...", "label": "..."}],',
        '  "study_slots": [...],',
        '  "commute_suggestion": {"leave_by": "...", "leave_by_label": "...", "reason": "..."},',
        '  "summary": "..."',
        "}"
    ])

    return "\n".join(prompt_parts)
