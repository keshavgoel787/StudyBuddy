from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.user_token import UserToken
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
    """
    try:
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
            date=datetime.now().strftime("%Y-%m-%d"),
            events=events,
            free_blocks=free_blocks,
            commute_duration_minutes=30
        )

        return DayPlanResponse(
            date=datetime.now().strftime("%Y-%m-%d"),
            events=events,
            free_blocks=free_blocks,
            recommendations=recommendations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate day plan: {str(e)}")
