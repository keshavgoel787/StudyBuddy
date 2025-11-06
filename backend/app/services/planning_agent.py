"""
Planning agent that uses Gemini to make intelligent scheduling decisions.
"""

from datetime import date
from typing import List, Tuple
from pydantic import BaseModel
import json

import google.generativeai as genai
from app.config import get_settings
from app.schemas.calendar import CalendarEvent, FreeBlock
from app.models.assignment import Assignment
from app.services.assignment_scheduler import propose_assignment_blocks_for_today
from app.services.day_context import build_day_context, DayContext
from app.utils.logger import log_info, log_error, log_debug

settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)

# Planning constants
MIN_FREE_HOURS_PER_DAY = 3.0  # Preserve at least 3 hours of free time


class AgentDecision(BaseModel):
    """Decision made by the planning agent."""
    mode: str  # "OFF" | "LIGHT" | "NORMAL" | "HIGH"
    kept_block_ids: List[str]
    reason: str


def agent_filter_schedule_for_today(
    today: date,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    assignments: List[Assignment],
    exams: List[CalendarEvent] = None,
) -> Tuple[List[CalendarEvent], AgentDecision]:
    """
    Use Gemini to intelligently filter proposed assignment blocks for today.

    Process:
    1. Propose candidate assignment blocks for today
    2. Build a DayContext summarizing what the day would look like
    3. Ask Gemini to decide which blocks to keep (if any)
    4. Return (kept_blocks, decision)

    Args:
        today: The date to schedule for
        events: Existing calendar events (classes, commute, etc)
        free_blocks: Available free time slots
        assignments: List of user's assignments
        exams: Optional list of exam events

    Returns:
        Tuple of (kept_assignment_blocks, agent_decision)
    """
    if exams is None:
        exams = []

    log_info("planning_agent", "Starting intelligent scheduling", date=str(today))

    # Step 1: Propose candidate blocks
    candidate_blocks = propose_assignment_blocks_for_today(
        today=today,
        events=events,
        free_blocks=free_blocks,
        assignments=assignments,
    )

    log_info("planning_agent", "Scheduler proposed blocks", count=len(candidate_blocks))

    if not candidate_blocks:
        log_info("planning_agent", "No blocks proposed, returning empty schedule")
        return [], AgentDecision(
            mode="OFF",
            kept_block_ids=[],
            reason="No study blocks needed today - no assignments or no free time"
        )

    # Step 2: Build day context
    context = build_day_context(
        today=today,
        events=events,
        candidate_blocks=candidate_blocks,
        assignments=assignments,
        exams=exams,
    )

    log_debug("planning_agent", "Day context built",
             awake_hours=f"{context.total_awake_hours:.1f}h",
             busy_hours=f"{context.total_busy_hours:.1f}h",
             study_hours=f"{context.total_study_hours_if_applied:.1f}h",
             free_hours=f"{context.free_hours_if_applied:.1f}h",
             exam_within_2d=context.has_exam_within_2_days)

    # Step 3: Build prompt for Gemini
    prompt = build_planning_prompt(context, candidate_blocks)

    # Step 4: Call Gemini to make decision
    try:
        model = genai.GenerativeModel('gemini-flash-latest')

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent decisions
                response_mime_type="application/json"
            ),
            safety_settings=safety_settings
        )

        if not response.candidates:
            raise Exception("Gemini did not return any response")

        # Parse JSON response - safely extract text
        try:
            response_text = response.text
        except (TypeError, AttributeError, ValueError) as e:
            # If response.text fails, try to extract from parts directly
            if response.candidates and response.candidates[0].content.parts:
                try:
                    response_text = response.candidates[0].content.parts[0].text
                except Exception as parts_error:
                    raise Exception(f"Cannot extract text from Gemini response: {str(parts_error)}")
            else:
                raise Exception(f"Gemini response has no valid content: {str(e)}")

        result = json.loads(response_text)

        decision = AgentDecision(**result)

        log_info("planning_agent", "Decision made",
                mode=decision.mode,
                kept_blocks=len(decision.kept_block_ids),
                reason=decision.reason)

    except Exception as e:
        log_error("planning_agent", "Gemini call failed", e)
        # Fallback: keep all blocks in NORMAL mode
        decision = AgentDecision(
            mode="NORMAL",
            kept_block_ids=[b.id for b in candidate_blocks],
            reason=f"Gemini unavailable, keeping all proposed blocks. Error: {str(e)}"
        )

    # Step 5: Filter blocks based on decision
    kept_ids = set(decision.kept_block_ids)
    kept_blocks = [b for b in candidate_blocks if b.id and b.id in kept_ids]

    log_info("planning_agent", "Returning kept blocks", count=len(kept_blocks))

    return kept_blocks, decision


def build_planning_prompt(context: DayContext, candidate_blocks: List[CalendarEvent]) -> str:
    """Build concise prompt for Gemini planning decisions."""

    # Compact block formatting
    blocks_list = []
    for block in candidate_blocks:
        import re
        due_days = ""
        if match := re.search(r'in (\d+) days', block.description):
            due_days = f", due in {match.group(1)}d"

        blocks_list.append(
            f"{block.id}: {block.start.strftime('%I:%M%p')}-{block.end.strftime('%I:%M%p')}{due_days}"
        )

    # Compact assignments formatting
    assignments_list = [
        f"{a['title']} (due {a['due_in_days']}d, {a['estimated_hours']}h, P{a['priority']})"
        for a in context.assignments_summary
    ]

    prompt = f"""Study planner for pre-med student. Balance productivity + rest.

**Context ({context.date})**
Awake: {context.total_awake_hours:.0f}h | If all blocks applied → Busy: {context.total_busy_hours:.0f}h, Study: {context.total_study_hours_if_applied:.0f}h, Free: {context.free_hours_if_applied:.0f}h
Exam <2d: {"YES" if context.has_exam_within_2_days else "NO"} | Next exam: {context.days_until_next_exam if context.days_until_next_exam else "none"}d

**Assignments:** {", ".join(assignments_list) if assignments_list else "None"}

**Proposed Blocks:** {" | ".join(blocks_list) if blocks_list else "None"}

**Modes:** OFF(0h), LIGHT(0-1h), NORMAL(1-3h), HIGH(3-5h exam prep)
**Rules:** Keep ≥{MIN_FREE_HOURS_PER_DAY}h free (unless exam), prioritize urgent, avoid overload

Return JSON:
{{
  "mode": "OFF"|"LIGHT"|"NORMAL"|"HIGH",
  "kept_block_ids": ["id1", "id2"],
  "reason": "Brief explanation"
}}"""

    return prompt
