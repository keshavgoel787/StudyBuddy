from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.models.user_token import UserToken
from app.models.day_plan import DayPlan
from app.models.user_bus_preferences import UserBusPreferences
from app.models.assignment import Assignment
from app.schemas.calendar import DayPlanResponse
from app.schemas.bus import BusPreferencesUpdate, BusPreferencesResponse
from app.utils.auth_middleware import get_current_user
from app.utils.time_utils import calculate_free_blocks
from app.utils.token_refresh import get_valid_user_token
from app.services.google_calendar import get_todays_events
from app.services.gemini_service import generate_day_plan
from app.services.bus_service import get_bus_suggestions_for_day, get_all_buses_for_day
from app.services.assignment_scheduler import schedule_assignments_for_today
from app.services.planning_agent import agent_filter_schedule_for_today

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/day-plan", response_model=DayPlanResponse)
async def get_day_plan(
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get today's events + AI-generated day plan with recommendations.
    Uses cached plan if available for today, otherwise generates new one.

    Query params:
    - force_refresh: Set to true to bypass cache and regenerate plan
    """
    try:
        today = date.today()

        # Check if we have a cached plan for today (skip if force_refresh is True)
        cached_plan = None
        if not force_refresh:
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

        # Ensure token is valid (refresh if expired)
        user_token = get_valid_user_token(user_token, db)

        # Fetch events from Google Calendar (async wrapper for blocking call)
        import asyncio
        events = await asyncio.to_thread(
            get_todays_events,
            user_token.access_token,
            user_token.refresh_token
        )

        # Calculate free blocks (fast, no need for async)
        free_blocks = calculate_free_blocks(events)

        # Fetch incomplete assignments for current user
        assignments = db.query(Assignment).filter(
            Assignment.user_id == current_user.id,
            Assignment.completed == False,
        ).all()

        # Use planning agent to intelligently schedule assignment blocks
        kept_assignment_blocks, agent_decision = agent_filter_schedule_for_today(
            today=today,
            events=events,
            free_blocks=free_blocks,
            assignments=assignments,
        )

        # Merge only kept assignment blocks into main events list
        events.extend(kept_assignment_blocks)
        # Resort by start time
        events = sorted(events, key=lambda e: e.start)

        # Recompute free_blocks after adding assignment blocks
        free_blocks = calculate_free_blocks(events)

        # Get bus suggestions based on events
        import sys
        try:
            print("\n" + "="*80, file=sys.stderr)
            print(f"DEBUG: Getting bus suggestions for {len(events)} events", file=sys.stderr)
            for e in events:
                print(f"  - {e.title}: {e.start}", file=sys.stderr)

            morning_bus, evening_bus = get_bus_suggestions_for_day(
                db=db,
                user_id=str(current_user.id),
                date=today,
                events=events
            )

            if morning_bus:
                print(f"DEBUG: Morning bus - Depart: {morning_bus.departure_time}, Arrive: {morning_bus.arrival_time}", file=sys.stderr)
            else:
                print(f"DEBUG: No morning bus found", file=sys.stderr)

            if evening_bus:
                print(f"DEBUG: Evening bus - Depart: {evening_bus.departure_time}, Arrive: {evening_bus.arrival_time}", file=sys.stderr)
            else:
                print(f"DEBUG: No evening bus found", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
        except Exception as bus_error:
            print(f"ERROR in get_bus_suggestions_for_day: {bus_error}", file=sys.stderr)
            print(f"Events: {[(e.title, e.start, e.start.tzinfo) for e in events]}", file=sys.stderr)
            raise

        # Convert bus suggestions to dict format
        bus_suggestions = {}
        if morning_bus:
            bus_suggestions["morning"] = morning_bus.to_dict(today)
        if evening_bus:
            bus_suggestions["evening"] = evening_bus.to_dict(today)

        # Format bus times for AI summary
        morning_bus_time = None
        evening_bus_time = None
        if morning_bus:
            morning_bus_time = f"{morning_bus.departure_time.strftime('%I:%M %p')} (arrives {morning_bus.arrival_time.strftime('%I:%M %p')})"
        if evening_bus:
            evening_bus_time = f"{evening_bus.departure_time.strftime('%I:%M %p')} (arrives {evening_bus.arrival_time.strftime('%I:%M %p')})"

        # Generate AI recommendations (async wrapper for blocking Gemini call)
        recommendations = await asyncio.to_thread(
            generate_day_plan,
            date=today.strftime("%Y-%m-%d"),
            events=events,
            free_blocks=free_blocks,
            commute_duration_minutes=30,
            morning_bus_time=morning_bus_time,
            evening_bus_time=evening_bus_time,
            planning_mode=agent_decision.mode,
            planning_reason=agent_decision.reason
        )

        # Add bus suggestions to recommendations
        recommendations.bus_suggestions = bus_suggestions if bus_suggestions else None

        # Convert Pydantic models to dicts for JSON storage
        events_dict = [event.model_dump(mode='json') for event in events]
        free_blocks_dict = [block.model_dump(mode='json') for block in free_blocks]
        recommendations_dict = recommendations.model_dump(mode='json')

        # Delete old cached plan for today if it exists (for force_refresh case)
        db.query(DayPlan).filter(
            DayPlan.user_id == current_user.id,
            DayPlan.date == today
        ).delete()

        # Cache the new plan
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
        import traceback
        print(f"ERROR in get_day_plan: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate day plan: {str(e)}")


@router.get("/bus-schedule")
async def get_bus_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available bus times for today.
    Returns outbound (Main & Murray → UDC) and inbound (UDC → Main & Murray) schedules.
    """
    try:
        today = date.today()
        schedule = get_all_buses_for_day(db, today)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bus schedule: {str(e)}")


@router.get("/bus-preferences", response_model=BusPreferencesResponse)
async def get_bus_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's bus preferences.
    """
    try:
        prefs = db.query(UserBusPreferences).filter(
            UserBusPreferences.user_id == current_user.id
        ).first()

        if not prefs:
            # Return defaults if no preferences set
            return BusPreferencesResponse(
                auto_create_events=False,
                arrival_buffer_minutes=15,
                departure_buffer_minutes=0
            )

        return BusPreferencesResponse(
            auto_create_events=prefs.auto_create_events,
            arrival_buffer_minutes=prefs.arrival_buffer_minutes,
            departure_buffer_minutes=prefs.departure_buffer_minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bus preferences: {str(e)}")


@router.post("/bus-preferences", response_model=BusPreferencesResponse)
async def update_bus_preferences(
    preferences: BusPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's bus preferences.
    """
    try:
        prefs = db.query(UserBusPreferences).filter(
            UserBusPreferences.user_id == current_user.id
        ).first()

        if not prefs:
            # Create new preferences
            prefs = UserBusPreferences(
                user_id=current_user.id,
                auto_create_events=preferences.auto_create_events if preferences.auto_create_events is not None else False,
                arrival_buffer_minutes=preferences.arrival_buffer_minutes if preferences.arrival_buffer_minutes is not None else 15,
                departure_buffer_minutes=preferences.departure_buffer_minutes if preferences.departure_buffer_minutes is not None else 0
            )
            db.add(prefs)
        else:
            # Update existing preferences
            if preferences.auto_create_events is not None:
                prefs.auto_create_events = preferences.auto_create_events
            if preferences.arrival_buffer_minutes is not None:
                prefs.arrival_buffer_minutes = preferences.arrival_buffer_minutes
            if preferences.departure_buffer_minutes is not None:
                prefs.departure_buffer_minutes = preferences.departure_buffer_minutes

        db.commit()
        db.refresh(prefs)

        return BusPreferencesResponse(
            auto_create_events=prefs.auto_create_events,
            arrival_buffer_minutes=prefs.arrival_buffer_minutes,
            departure_buffer_minutes=prefs.departure_buffer_minutes
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update bus preferences: {str(e)}")
