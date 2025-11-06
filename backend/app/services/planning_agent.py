"""
Planning agent that uses Gemini to make intelligent scheduling decisions.
"""

from datetime import date
from typing import List, Tuple
from pydantic import BaseModel
import json
import sys

import google.generativeai as genai
from app.config import get_settings
from app.schemas.calendar import CalendarEvent, FreeBlock
from app.models.assignment import Assignment
from app.services.assignment_scheduler import propose_assignment_blocks_for_today
from app.services.day_context import build_day_context, DayContext

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

    print(f"\n[Planning Agent] Starting intelligent scheduling for {today}", file=sys.stderr)

    # Step 1: Propose candidate blocks
    candidate_blocks = propose_assignment_blocks_for_today(
        today=today,
        events=events,
        free_blocks=free_blocks,
        assignments=assignments,
    )

    print(f"[Planning Agent] Scheduler proposed {len(candidate_blocks)} blocks", file=sys.stderr)

    if not candidate_blocks:
        print(f"[Planning Agent] No blocks proposed, returning empty schedule", file=sys.stderr)
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

    print(f"[Planning Agent] Day Context:", file=sys.stderr)
    print(f"  - Total awake hours: {context.total_awake_hours:.1f}h", file=sys.stderr)
    print(f"  - Busy hours (if applied): {context.total_busy_hours:.1f}h", file=sys.stderr)
    print(f"  - Study hours (if applied): {context.total_study_hours_if_applied:.1f}h", file=sys.stderr)
    print(f"  - Free hours (if applied): {context.free_hours_if_applied:.1f}h", file=sys.stderr)
    print(f"  - Exam within 2 days: {context.has_exam_within_2_days}", file=sys.stderr)

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

        print(f"[Planning Agent] Decision: mode={decision.mode}, keeping {len(decision.kept_block_ids)} blocks", file=sys.stderr)
        print(f"[Planning Agent] Reason: {decision.reason}", file=sys.stderr)

    except Exception as e:
        print(f"[Planning Agent] ERROR calling Gemini: {str(e)}", file=sys.stderr)
        # Fallback: keep all blocks in NORMAL mode
        decision = AgentDecision(
            mode="NORMAL",
            kept_block_ids=[b.id for b in candidate_blocks],
            reason=f"Gemini unavailable, keeping all proposed blocks. Error: {str(e)}"
        )

    # Step 5: Filter blocks based on decision
    kept_ids = set(decision.kept_block_ids)
    kept_blocks = [b for b in candidate_blocks if b.id and b.id in kept_ids]

    print(f"[Planning Agent] Returning {len(kept_blocks)} kept blocks\n", file=sys.stderr)

    return kept_blocks, decision


def build_planning_prompt(context: DayContext, candidate_blocks: List[CalendarEvent]) -> str:
    """Build the prompt for Gemini to make planning decisions."""

    # Format candidate blocks
    blocks_text = ""
    for block in candidate_blocks:
        # Extract assignment title from block title ("Work on X" -> "X")
        assignment_title = block.title.replace("Work on ", "")

        # Extract due date info from description
        due_info = ""
        if "in" in block.description and "days" in block.description:
            import re
            match = re.search(r'in (\d+) days', block.description)
            if match:
                due_info = f"due in {match.group(1)} days"

        blocks_text += f"- ID: {block.id}\n"
        blocks_text += f"  Title: {block.title}\n"
        blocks_text += f"  Time: {block.start.strftime('%I:%M %p')} - {block.end.strftime('%I:%M %p')}\n"
        blocks_text += f"  Assignment: {assignment_title} ({due_info})\n\n"

    # Format assignments summary
    assignments_text = ""
    for a in context.assignments_summary:
        assignments_text += f"- {a['title']}: due in {a['due_in_days']} days, est. {a['estimated_hours']}h (priority {a['priority']})\n"

    prompt = f"""You are an intelligent study planning assistant. Your job is to help a pre-med student maintain a healthy balance between productivity and rest.

## Today's Context ({context.date})

**Time Breakdown:**
- Total awake hours: {context.total_awake_hours:.1f}h ({8} AM - {23} PM)
- If all proposed blocks are kept:
  - Busy hours: {context.total_busy_hours:.1f}h
  - Study hours: {context.total_study_hours_if_applied:.1f}h
  - Free hours: {context.free_hours_if_applied:.1f}h

**Urgency Factors:**
- Exam within 2 days: {"YES" if context.has_exam_within_2_days else "NO"}
- Days until next exam: {context.days_until_next_exam if context.days_until_next_exam is not None else "none scheduled"}

**Assignments:**
{assignments_text if assignments_text else "No assignments"}

**Proposed Study Blocks:**
{blocks_text}

## Your Task

Decide which blocks to keep for today based on these guidelines:

**Intensity Modes:**
- **OFF** (0h): No study blocks. Use when day is already full or student needs rest.
- **LIGHT** (0-1h): Minimal study. Use for low-urgency days or when free time is limited.
- **NORMAL** (1-3h): Balanced study. Default for typical days with moderate deadlines.
- **HIGH** (3-5h): Intensive study. Only when exam ≤2 days or critical deadline very soon.

**Rules:**
1. **Preserve free time**: Keep at least {MIN_FREE_HOURS_PER_DAY}h free unless exam is within 2 days
2. **Prioritize urgency**: Focus on assignments due soonest
3. **Don't overload**: It's better to drop blocks than to overwhelm the student
4. **Be realistic**: If today is already packed, suggest OFF or LIGHT mode
5. **Consider energy**: Morning/afternoon blocks are generally better than late night

## Response Format

Return JSON with:
- `mode`: One of "OFF", "LIGHT", "NORMAL", "HIGH"
- `kept_block_ids`: Array of block IDs to keep (empty array = no blocks)
- `reason`: 1-2 sentence explanation of your decision

Example:
{{
  "mode": "LIGHT",
  "kept_block_ids": ["assignment-1-0"],
  "reason": "Day is already busy with classes. Keeping one morning block for the assignment due tomorrow, dropping others to preserve evening free time."
}}

Make your decision now:"""

    return prompt
