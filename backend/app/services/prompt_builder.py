"""
Optimized prompt builders for Gemini AI.
Separates prompt logic from service logic for better maintainability.
"""

from typing import List
from datetime import datetime, date
import re

from app.schemas.calendar import CalendarEvent, FreeBlock
from app.models.assignment import Assignment


def build_day_plan_prompt(
    date: str,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    assignments: List[Assignment] = None,
    morning_bus_time: str = None,
    evening_bus_time: str = None,
    planning_mode: str = None,
    planning_reason: str = None
) -> str:
    """Build optimized prompt for day plan generation with assignment intelligence."""

    # Partition events efficiently
    assignment_events = [e for e in events if getattr(e, 'event_type', 'calendar') == "assignment"]
    calendar_events = [e for e in events if getattr(e, 'event_type', 'calendar') == "calendar"]

    # Analyze upcoming assignments by type and urgency
    today = datetime.fromisoformat(date).date()
    upcoming_exams = []
    upcoming_quizzes = []
    upcoming_other = []

    if assignments:
        for assignment in assignments:
            if assignment.completed:
                continue

            # Calculate days until due
            due_date = assignment.due_date.date() if hasattr(assignment.due_date, 'date') else assignment.due_date
            days_until_due = (due_date - today).days

            # Categorize by type and urgency
            assignment_info = {
                'title': assignment.title,
                'type': assignment.assignment_type or 'assignment',
                'days_until_due': days_until_due,
                'priority': assignment.priority
            }

            # Skip if too far in future (>14 days)
            if days_until_due > 14:
                continue

            # Categorize by type
            atype = (assignment.assignment_type or '').lower()
            if 'exam' in atype:
                upcoming_exams.append(assignment_info)
            elif 'quiz' in atype:
                upcoming_quizzes.append(assignment_info)
            else:
                upcoming_other.append(assignment_info)

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

    # Add upcoming assignment urgency context
    if upcoming_exams or upcoming_quizzes or upcoming_other:
        prompt_parts.append("")
        prompt_parts.append("**Upcoming Assignments:**")

        # Very urgent exams (0-5 days)
        urgent_exams = [a for a in upcoming_exams if a['days_until_due'] <= 5]
        if urgent_exams:
            exam_list = [f"{a['title']} in {a['days_until_due']}d" for a in urgent_exams]
            prompt_parts.append(f"- URGENT EXAMS: {', '.join(exam_list)}")

        # Upcoming exams (6-14 days)
        future_exams = [a for a in upcoming_exams if a['days_until_due'] > 5]
        if future_exams:
            exam_list = [f"{a['title']} in {a['days_until_due']}d" for a in future_exams]
            prompt_parts.append(f"- Upcoming exams: {', '.join(exam_list)}")

        # Urgent quizzes (0-3 days)
        urgent_quizzes = [a for a in upcoming_quizzes if a['days_until_due'] <= 3]
        if urgent_quizzes:
            quiz_list = [f"{a['title']} in {a['days_until_due']}d" for a in urgent_quizzes]
            prompt_parts.append(f"- Urgent quizzes: {', '.join(quiz_list)}")

        # High priority other assignments (0-5 days)
        urgent_other = [a for a in upcoming_other if a['days_until_due'] <= 5 and a['priority'] >= 2]
        if urgent_other:
            other_list = [f"{a['title']} ({a['type']}) in {a['days_until_due']}d" for a in urgent_other]
            prompt_parts.append(f"- Other urgent: {', '.join(other_list)}")

    if morning_bus_time or evening_bus_time:
        bus_times = []
        if morning_bus_time:
            bus_times.append(f"To campus: {morning_bus_time}")
        if evening_bus_time:
            bus_times.append(f"From campus: {evening_bus_time}")
        prompt_parts.append(f"**Bus:** {' | '.join(bus_times)}")

    if planning_mode and planning_reason:
        prompt_parts.append(f"**Planning Mode:** {planning_mode} - {planning_reason}")

    # Build smart study slot guidance based on urgency
    study_guidance = []
    if urgent_exams:
        study_guidance.append("**PRIORITY**: Exams in 0-5 days require intensive study blocks (1-2 hours)")
    elif urgent_quizzes:
        study_guidance.append("Quizzes in 0-3 days benefit from focused review blocks (30-60 min)")
    elif urgent_other:
        study_guidance.append("High-priority assignments due soon need attention")
    elif future_exams:
        study_guidance.append("Exams 6-14 days out: light study blocks OK but not urgent")
    else:
        study_guidance.append("No urgent assignments: study blocks optional")

    prompt_parts.extend([
        "",
        "Generate personalized day plan for Dippi:",
        "1. **Lunch slots**: Suggest 1-2 realistic lunch times (11AM-2PM, 30-60min) based on class schedule. If no classes, suggest just ONE midday lunch.",
        "",
        "2. **Study slots** - BE SMART about assignment urgency:",
        *[f"   {g}" for g in study_guidance],
        "   - If scheduled study blocks already exist, leave study_slots EMPTY",
        "   - Exams (0-5 days): Suggest 1-2 study blocks (1-2h each) if free time exists",
        "   - Quizzes (0-3 days): Suggest 1 focused block (30-60min)",
        "   - Lab reports/essays (0-5 days, high priority): Suggest 1 block (1-2h)",
        "   - Homework (0-3 days): Suggest 1 short block (30-60min)",
        "   - Assignments >5 days OR already scheduled: SKIP, leave empty",
        "   - No assignments or light day: SKIP, leave empty",
        "",
        "3. **Commute**: If bus times provided, remind about commute. Otherwise omit.",
        "",
        "4. **Summary**: Warm, friendly message starting with 'Hey Dippi,' that:",
        "   - Mentions any urgent exams/quizzes and encourages focused study if needed",
        "   - Highlights scheduled study blocks if any exist",
        "   - Mentions bus/commute times if relevant",
        "   - If day is light/no urgent work: encourage her to relax and enjoy free time",
        "   - End with '<3' or similar warm sign-off",
        "",
        f"JSON format (use date {date} for all datetimes):",
        "{",
        f'  "lunch_slots": [{{"start": "{date}T12:00:00", "end": "{date}T13:00:00", "label": "12:00 PM - 1:00 PM"}}],',
        '  "study_slots": [],  // BE SELECTIVE based on urgency rules above',
        f'  "commute_suggestion": {{"leave_by": "{date}T19:15:00", "leave_by_label": "7:15 PM", "reason": "Catch evening bus home"}} OR null,',
        '  "summary": "Hey Dippi, ..."',
        "}"
    ])

    return "\n".join(prompt_parts)
