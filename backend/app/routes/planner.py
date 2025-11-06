"""
Planner API endpoints for intelligent assignment scheduling.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
import asyncio

from app.database import get_db
from app.models.user import User
from app.models.user_token import UserToken
from app.models.assignment import Assignment
from app.utils.auth_middleware import get_current_user
from app.utils.time_utils import calculate_free_blocks
from app.utils.token_refresh import get_valid_user_token
from app.services.google_calendar import get_todays_events
from app.services.planning_agent import agent_filter_schedule_for_today, AgentDecision

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/assignments/{assignment_id}/autoschedule-today")
async def autoschedule_assignment_today(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Runs the planning agent for a specific assignment only.
    Returns decision + blocks without modifying the cache.

    This is useful for the "Auto-schedule today" button on individual assignments.
    """
    try:
        today = date.today()

        # Fetch the specific assignment
        assignment = db.query(Assignment).filter(
            Assignment.id == assignment_id,
            Assignment.user_id == current_user.id,
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if assignment.completed:
            return {
                "decision": "SKIPPED",
                "reason": "Assignment is already completed",
                "blocks": []
            }

        # Get user's Google Calendar events
        user_token = db.query(UserToken).filter(UserToken.user_id == current_user.id).first()

        if not user_token:
            raise HTTPException(status_code=401, detail="No Google Calendar access")

        user_token = get_valid_user_token(user_token, db)

        # Fetch today's events
        events = await asyncio.to_thread(
            get_todays_events,
            user_token.access_token,
            user_token.refresh_token
        )

        # Calculate free blocks
        free_blocks = calculate_free_blocks(events)

        # Run planning agent with only this assignment
        kept_blocks, agent_decision = agent_filter_schedule_for_today(
            today=today,
            events=events,
            free_blocks=free_blocks,
            assignments=[assignment],  # Only this assignment
        )

        # Convert blocks to dict format
        blocks_dict = [
            {
                "id": block.id,
                "title": block.title,
                "start": block.start.isoformat(),
                "end": block.end.isoformat(),
                "description": block.description,
                "event_type": block.event_type,
            }
            for block in kept_blocks
        ]

        return {
            "decision": agent_decision.mode,
            "reason": agent_decision.reason,
            "blocks": blocks_dict,
            "assignment": {
                "id": assignment.id,
                "title": assignment.title,
                "due_date": assignment.due_date.isoformat(),
                "estimated_hours": assignment.estimated_hours,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in autoschedule_assignment_today: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to auto-schedule assignment: {str(e)}")
