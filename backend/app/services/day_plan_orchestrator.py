"""
Orchestrator service for day plan generation.
Coordinates all services in an efficient, modular way.
"""

from datetime import date
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.schemas.calendar import CalendarEvent, FreeBlock, Recommendations
from app.models.assignment import Assignment
from app.utils.time_utils import calculate_free_blocks
from app.services.planning_agent import agent_filter_schedule_for_today, AgentDecision
from app.services.bus_service import get_bus_suggestions_for_day, BusSuggestion
from app.services.gemini_service import generate_day_plan


class DayPlanData:
    """Container for all day plan data to avoid passing many parameters."""

    def __init__(
        self,
        today: date,
        events: List[CalendarEvent],
        assignments: List[Assignment],
    ):
        self.today = today
        self.events = events
        self.assignments = assignments
        self.free_blocks: List[FreeBlock] = []
        self.assignment_blocks: List[CalendarEvent] = []
        self.agent_decision: Optional[AgentDecision] = None
        self.morning_bus: Optional[BusSuggestion] = None
        self.evening_bus: Optional[BusSuggestion] = None
        self.recommendations: Optional[Recommendations] = None


def orchestrate_day_plan(
    db: Session,
    user_id: str,
    today: date,
    events: List[CalendarEvent],
    assignments: List[Assignment],
) -> Tuple[List[CalendarEvent], List[FreeBlock], Recommendations]:
    """
    Main orchestrator for day plan generation.
    Coordinates all services efficiently with minimal redundancy.

    Returns:
        (final_events, final_free_blocks, recommendations)
    """

    data = DayPlanData(today, events, assignments)

    # Step 1: Calculate initial free blocks
    data.free_blocks = calculate_free_blocks(data.events)

    # Step 2: Run planning agent (includes scheduler + Gemini decision)
    data.assignment_blocks, data.agent_decision = agent_filter_schedule_for_today(
        today=data.today,
        events=data.events,
        free_blocks=data.free_blocks,
        assignments=data.assignments,
    )

    # Step 3: Merge assignment blocks and recalculate free blocks
    data.events.extend(data.assignment_blocks)
    data.events.sort(key=lambda e: e.start)
    data.free_blocks = calculate_free_blocks(data.events)

    # Step 4: Get bus suggestions (only if needed based on events)
    data.morning_bus, data.evening_bus = get_bus_suggestions_for_day(
        db=db,
        user_id=user_id,
        date=data.today,
        events=data.events
    )

    # Step 5: Generate AI recommendations with all context
    data.recommendations = _generate_recommendations(data)

    # Step 6: Add bus suggestions to recommendations
    if data.morning_bus or data.evening_bus:
        data.recommendations.bus_suggestions = _format_bus_suggestions(
            data.morning_bus,
            data.evening_bus,
            data.today
        )

    return data.events, data.free_blocks, data.recommendations


def _generate_recommendations(data: DayPlanData) -> Recommendations:
    """Generate AI recommendations with formatted inputs."""

    # Format bus times for AI (only if they exist)
    morning_bus_time = None
    evening_bus_time = None

    if data.morning_bus:
        morning_bus_time = (
            f"{data.morning_bus.departure_time.strftime('%I:%M %p')} "
            f"(arrives {data.morning_bus.arrival_time.strftime('%I:%M %p')})"
        )

    if data.evening_bus:
        evening_bus_time = (
            f"{data.evening_bus.departure_time.strftime('%I:%M %p')} "
            f"(arrives {data.evening_bus.arrival_time.strftime('%I:%M %p')})"
        )

    # Call Gemini with minimal, well-structured data
    return generate_day_plan(
        date=data.today.strftime("%Y-%m-%d"),
        events=data.events,
        free_blocks=data.free_blocks,
        assignments=data.assignments,
        commute_duration_minutes=30,
        morning_bus_time=morning_bus_time,
        evening_bus_time=evening_bus_time,
        planning_mode=data.agent_decision.mode if data.agent_decision else None,
        planning_reason=data.agent_decision.reason if data.agent_decision else None
    )


def _format_bus_suggestions(
    morning_bus: Optional[BusSuggestion],
    evening_bus: Optional[BusSuggestion],
    today: date
) -> dict:
    """Convert bus suggestions to dict format for API response."""

    result = {}

    if morning_bus:
        result["morning"] = morning_bus.to_dict(today)

    if evening_bus:
        result["evening"] = evening_bus.to_dict(today)

    return result if result else None
