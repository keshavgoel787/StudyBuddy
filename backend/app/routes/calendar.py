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
from app.schemas.events import (
    EventCreate, EventCreateResponse, EventDeleteResponse,
    SyncAssignmentBlockRequest, SyncBusRequest
)
from app.utils.auth_middleware import get_current_user
from app.utils.token_refresh import get_valid_user_token
from app.utils.cache import cleanup_old_day_plans
from app.services.google_calendar import (
    get_todays_events, create_calendar_event,
    create_assignment_block_event, create_bus_event, delete_calendar_event
)
from app.services.bus_service import get_all_buses_for_day
from app.services.day_plan_orchestrator import orchestrate_day_plan

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _get_user_calendar_token(user_id: str, db: Session) -> UserToken:
    """
    Helper function to get and validate user's calendar access token.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Valid UserToken object

    Raises:
        HTTPException: If no token found or validation fails
    """
    user_token = db.query(UserToken).filter(UserToken.user_id == user_id).first()

    if not user_token:
        raise HTTPException(status_code=401, detail="No Google Calendar access. Please sign in again.")

    # Ensure token is valid (refresh if expired)
    return get_valid_user_token(user_token, db)


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

        # Opportunistic cleanup: Remove day plans older than 7 days (run in background)
        # This prevents database bloat without impacting response time
        import asyncio
        asyncio.create_task(asyncio.to_thread(cleanup_old_day_plans, db, days_to_keep=7))

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
        # Get user's validated Google tokens
        user_token = _get_user_calendar_token(str(current_user.id), db)

        # Fetch events from Google Calendar (async wrapper for blocking call)
        import asyncio
        events = await asyncio.to_thread(
            get_todays_events,
            user_token.access_token,
            user_token.refresh_token
        )

        # Fetch incomplete assignments
        assignments = db.query(Assignment).filter(
            Assignment.user_id == current_user.id,
            Assignment.completed == False,
        ).all()

        # Orchestrate entire day plan generation (efficient, modular)
        events, free_blocks, recommendations = await asyncio.to_thread(
            orchestrate_day_plan,
            db=db,
            user_id=str(current_user.id),
            today=today,
            events=events,
            assignments=assignments,
        )

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


@router.post("/events/create", response_model=EventCreateResponse)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a custom event in Google Calendar.

    This allows users to add any event directly from the dashboard.
    """
    try:
        # Get user's validated Google tokens
        user_token = _get_user_calendar_token(str(current_user.id), db)

        # Create the event
        event_id = create_calendar_event(
            access_token=user_token.access_token,
            title=event.title,
            start_time=event.start_time,
            end_time=event.end_time,
            description=event.description,
            location=event.location,
            color_id=event.color_id,
            refresh_token=user_token.refresh_token
        )

        return EventCreateResponse(
            event_id=event_id,
            message=f"Event '{event.title}' created successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


@router.post("/events/sync-assignment-block", response_model=EventCreateResponse)
async def sync_assignment_block(
    request: SyncAssignmentBlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync an assignment study block to Google Calendar.

    Creates a purple study block event with assignment details.
    """
    try:
        # Get user's validated Google tokens
        user_token = _get_user_calendar_token(str(current_user.id), db)

        # Get assignment details
        assignment = db.query(Assignment).filter(
            Assignment.id == request.assignment_id,
            Assignment.user_id == current_user.id
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Create the event
        event_id = create_assignment_block_event(
            access_token=user_token.access_token,
            assignment_title=assignment.title,
            start_time=request.start_time,
            end_time=request.end_time,
            due_date=assignment.due_date,
            refresh_token=user_token.refresh_token
        )

        return EventCreateResponse(
            event_id=event_id,
            message=f"Study block for '{assignment.title}' added to calendar"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync assignment block: {str(e)}")


@router.post("/events/sync-bus", response_model=EventCreateResponse)
async def sync_bus(
    request: SyncBusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync a bus suggestion to Google Calendar.

    Creates a blue commute event with bus details.
    """
    try:
        # Get user's validated Google tokens
        user_token = _get_user_calendar_token(str(current_user.id), db)

        # Determine locations based on direction
        if request.direction == "outbound":
            departure_location = "Main & Murray"
            arrival_location = "UDC"
        else:
            departure_location = "UDC"
            arrival_location = "Main & Murray"

        # Create the event
        event_id = create_bus_event(
            access_token=user_token.access_token,
            direction=request.direction,
            departure_time=request.departure_time,
            arrival_time=request.arrival_time,
            departure_location=departure_location,
            arrival_location=arrival_location,
            refresh_token=user_token.refresh_token
        )

        return EventCreateResponse(
            event_id=event_id,
            message=f"Bus event added to calendar"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync bus: {str(e)}")


@router.delete("/events/{event_id}", response_model=EventDeleteResponse)
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an event from Google Calendar.

    This endpoint allows users to delete any event from their Google Calendar,
    including custom events, synced assignment blocks, and synced bus events.

    Args:
        event_id: The Google Calendar event ID to delete
        current_user: Authenticated user
        db: Database session

    Returns:
        EventDeleteResponse with success status and message

    Raises:
        HTTPException 401: If user has no Google Calendar access
        HTTPException 404: If event not found or user doesn't have permission
        HTTPException 500: If deletion fails
    """
    try:
        # Get user's calendar access token
        user_token = _get_user_calendar_token(current_user.id, db)

        # Delete the event from Google Calendar
        delete_calendar_event(
            access_token=user_token.access_token,
            event_id=event_id,
            refresh_token=user_token.refresh_token
        )

        return EventDeleteResponse(
            success=True,
            message="Event deleted from Google Calendar"
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()

        # Handle 404 not found errors
        if "not found" in error_msg or "404" in error_msg:
            raise HTTPException(
                status_code=404,
                detail="Event not found or you don't have permission to delete it"
            )

        # Handle other errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete event: {str(e)}"
        )
