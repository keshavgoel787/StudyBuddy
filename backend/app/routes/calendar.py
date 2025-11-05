from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.models.user_token import UserToken
from app.models.day_plan import DayPlan
from app.schemas.calendar import TodayResponse, DayPlanResponse
from app.utils.auth_middleware import get_current_user
from app.utils.time_utils import calculate_free_blocks
from app.services.google_calendar import get_todays_events
from app.services.gemini_service import generate_day_plan

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/today", response_model=TodayResponse)
async def get_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get today's calendar events from Google Calendar.
    """
    try:
        # Get user's Google tokens
        user_token = db.query(UserToken).filter(UserToken.user_id == current_user.id).first()

        if not user_token:
            raise HTTPException(status_code=401, detail="No Google Calendar access. Please sign in again.")

        # Fetch events from Google Calendar
        events = get_todays_events(user_token.access_token, user_token.refresh_token)

        return TodayResponse(
            date=datetime.now().strftime("%Y-%m-%d"),
            events=events
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar: {str(e)}")


@router.get("/day-plan", response_model=DayPlanResponse)
async def get_day_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get today's events + AI-generated day plan with recommendations.
    Uses cached plan if available for today, otherwise generates new one.
    """
    try:
        today = date.today()

        # Check if we have a cached plan for today
        cached_plan = db.query(DayPlan).filter(
            DayPlan.user_id == current_user.id,
            DayPlan.date == today
        ).first()

        if cached_plan:
            # Convert JSON back to Pydantic models
            from app.schemas.calendar import CalendarEvent, FreeBlock, Recommendations

            events = [CalendarEvent(**event) for event in cached_plan.events]
            free_blocks = [FreeBlock(**block) for block in cached_plan.free_blocks]
            recommendations = Recommendations(**cached_plan.recommendations)

            # Return cached plan
            return DayPlanResponse(
                date=today.strftime("%Y-%m-%d"),
                events=events,
                free_blocks=free_blocks,
                recommendations=recommendations
            )

        # No cached plan - generate new one
        # Get user's Google tokens
        user_token = db.query(UserToken).filter(UserToken.user_id == current_user.id).first()

        if not user_token:
            raise HTTPException(status_code=401, detail="No Google Calendar access. Please sign in again.")

        # Fetch events from Google Calendar
        events = get_todays_events(user_token.access_token, user_token.refresh_token)

        # Calculate free blocks
        free_blocks = calculate_free_blocks(events)

        # Generate AI recommendations
        recommendations = generate_day_plan(
            date=today.strftime("%Y-%m-%d"),
            events=events,
            free_blocks=free_blocks,
            commute_duration_minutes=30
        )

        # Convert Pydantic models to dicts for JSON storage
        events_dict = [event.model_dump(mode='json') for event in events]
        free_blocks_dict = [block.model_dump(mode='json') for block in free_blocks]
        recommendations_dict = recommendations.model_dump(mode='json')

        # Cache the plan
        day_plan = DayPlan(
            user_id=current_user.id,
            date=today,
            events=events_dict,
            free_blocks=free_blocks_dict,
            recommendations=recommendations_dict
        )
        db.add(day_plan)
        db.commit()

        return DayPlanResponse(
            date=today.strftime("%Y-%m-%d"),
            events=events,
            free_blocks=free_blocks,
            recommendations=recommendations
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate day plan: {str(e)}")
