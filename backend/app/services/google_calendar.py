from datetime import datetime, timedelta
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from zoneinfo import ZoneInfo
from app.schemas.calendar import CalendarEvent
from app.utils.logger import log_info, log_error


def _build_calendar_service(access_token: str, refresh_token: str = None):
    """
    Helper function to build Google Calendar API service.

    Args:
        access_token: Google OAuth access token
        refresh_token: Google OAuth refresh token (optional)

    Returns:
        Google Calendar API service object
    """
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,  # Not needed for API calls
        client_secret=None
    )
    return build('calendar', 'v3', credentials=creds)


def get_todays_events(access_token: str, refresh_token: str = None) -> List[CalendarEvent]:
    """
    Fetch today's events from Google Calendar.

    Args:
        access_token: Google OAuth access token
        refresh_token: Google OAuth refresh token (optional)

    Returns:
        List of CalendarEvent objects
    """
    try:
        # Build the Calendar API service
        service = _build_calendar_service(access_token, refresh_token)

        # Get today's date range in EST timezone
        # Import timezone utilities
        from zoneinfo import ZoneInfo
        from datetime import date as date_type

        # Define EST timezone
        est = ZoneInfo("America/New_York")

        # Get today in EST
        now_est = datetime.now(est)
        local_today = now_est.date()

        # Create start and end of today in EST, then convert to UTC for Google Calendar API
        today_start_est = datetime(local_today.year, local_today.month, local_today.day, 0, 0, 0, tzinfo=est)
        tomorrow = local_today + timedelta(days=1)
        tomorrow_start_est = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, tzinfo=est)

        # Convert to UTC for the API (Google Calendar expects UTC with 'Z' suffix)
        today_start = today_start_est.astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')
        today_end = tomorrow_start_est.astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')

        # Call the Calendar API
        events_result = service.events().list(
            calendarId='primary',
            timeMin=today_start,
            timeMax=today_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Convert to CalendarEvent objects
        calendar_events = []

        for event in events:
            # Handle both dateTime and date (all-day events)
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Parse datetime
            if 'T' in start:  # dateTime format
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

                # Convert to EST to check the date
                start_dt_est = start_dt.astimezone(est)
                event_date = start_dt_est.date()
            else:  # date format (all-day event)
                start_dt = datetime.fromisoformat(start + 'T00:00:00')
                end_dt = datetime.fromisoformat(end + 'T23:59:59')
                event_date = start_dt.date()

            # Filter: only include events that start today in EST
            if event_date != local_today:
                continue  # Skip events not starting today

            calendar_events.append(CalendarEvent(
                id=event['id'],
                title=event.get('summary', 'Untitled Event'),
                location=event.get('location'),
                start=start_dt,
                end=end_dt
            ))

        return calendar_events

    except Exception as e:
        raise Exception(f"Failed to fetch calendar events: {str(e)}")


def get_week_events(access_token: str, refresh_token: str = None, start_date: datetime = None) -> List[CalendarEvent]:
    """
    Fetch events for a week from Google Calendar (from all calendars).

    Args:
        access_token: Google OAuth access token
        refresh_token: Google OAuth refresh token (optional)
        start_date: Start date for the week (defaults to current week starting Sunday)

    Returns:
        List of CalendarEvent objects for the week
    """
    try:
        # Build the Calendar API service
        service = _build_calendar_service(access_token, refresh_token)

        # Define EST timezone
        est = ZoneInfo("America/New_York")

        # Get the start of the week (Sunday)
        if start_date is None:
            now_est = datetime.now(est)
            # Calculate days since Sunday (0 = Monday, 6 = Sunday)
            days_since_sunday = (now_est.weekday() + 1) % 7
            week_start = (now_est - timedelta(days=days_since_sunday)).date()
        else:
            week_start = start_date.date()

        # Create start and end of week in EST (Sunday to Saturday)
        week_start_est = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0, tzinfo=est)
        week_end_date = week_start + timedelta(days=7)
        week_end_est = datetime(week_end_date.year, week_end_date.month, week_end_date.day, 0, 0, 0, tzinfo=est)

        # Convert to UTC for the API
        week_start_utc = week_start_est.astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')
        week_end_utc = week_end_est.astimezone(ZoneInfo("UTC")).isoformat().replace('+00:00', 'Z')

        log_info("google_calendar", f"Fetching events from {week_start_utc} to {week_end_utc}")

        # Get list of all calendars
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])

        log_info("google_calendar", f"Found {len(calendars)} calendars")

        all_events = []

        # Fetch events from each calendar
        for calendar in calendars:
            calendar_id = calendar['id']
            calendar_name = calendar.get('summary', 'Unknown')

            # Skip holidays calendar
            if 'holiday' in calendar_name.lower():
                log_info("google_calendar", f"Skipping calendar '{calendar_name}'")
                continue

            try:
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=week_start_utc,
                    timeMax=week_end_utc,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()

                events = events_result.get('items', [])
                log_info("google_calendar", f"Found {len(events)} events in calendar '{calendar_name}'")

                # Convert to CalendarEvent objects
                for event in events:
                    # Handle both dateTime and date (all-day events)
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))

                    # Parse datetime
                    if 'T' in start:  # dateTime format
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    else:  # date format (all-day event) - add timezone
                        start_dt = datetime.fromisoformat(start + 'T00:00:00').replace(tzinfo=est)
                        end_dt = datetime.fromisoformat(end + 'T23:59:59').replace(tzinfo=est)

                    all_events.append(CalendarEvent(
                        id=event['id'],
                        title=event.get('summary', 'Untitled Event'),
                        location=event.get('location'),
                        start=start_dt,
                        end=end_dt
                    ))
            except Exception as e:
                log_error("google_calendar", f"Failed to fetch events from calendar '{calendar_name}': {str(e)}")
                # Continue with other calendars even if one fails

        log_info("google_calendar", f"Total events fetched from all calendars: {len(all_events)}")

        # Ensure all events have timezone-aware datetimes before sorting
        for event in all_events:
            if event.start.tzinfo is None:
                event.start = event.start.replace(tzinfo=est)
            if event.end.tzinfo is None:
                event.end = event.end.replace(tzinfo=est)

        # Sort events by start time
        all_events.sort(key=lambda e: e.start)

        return all_events

    except Exception as e:
        log_error("google_calendar", f"Failed to fetch week events: {str(e)}", e)
        raise Exception(f"Failed to fetch calendar events: {str(e)}")


def create_calendar_event(
    access_token: str,
    title: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    location: Optional[str] = None,
    color_id: Optional[str] = None,
    refresh_token: str = None
) -> str:
    """
    Create an event in the user's Google Calendar.

    Args:
        access_token: Google OAuth access token
        title: Event title/summary
        start_time: Event start (timezone-aware datetime)
        end_time: Event end (timezone-aware datetime)
        description: Event description (optional)
        location: Event location (optional)
        color_id: Google Calendar color ID (1-11, optional)
        refresh_token: Google OAuth refresh token (optional)

    Returns:
        Event ID of the created event

    Color IDs:
        1: Lavender, 2: Sage, 3: Grape, 4: Flamingo, 5: Banana,
        6: Tangerine, 7: Peacock, 8: Graphite, 9: Blueberry, 10: Basil, 11: Tomato
    """
    try:
        # Build the Calendar API service
        service = _build_calendar_service(access_token, refresh_token)

        # Convert times to RFC3339 format (Google Calendar expects this)
        # Ensure timezone-aware
        if start_time.tzinfo is None:
            est = ZoneInfo("America/New_York")
            start_time = start_time.replace(tzinfo=est)
        if end_time.tzinfo is None:
            est = ZoneInfo("America/New_York")
            end_time = end_time.replace(tzinfo=est)

        # Build event body
        event_body = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
        }

        # Add optional fields
        if description:
            event_body['description'] = description
        if location:
            event_body['location'] = location
        if color_id:
            event_body['colorId'] = str(color_id)

        # Create the event
        event = service.events().insert(calendarId='primary', body=event_body).execute()

        log_info("google_calendar", "Created event",
                event_id=event['id'],
                title=title)

        return event['id']

    except Exception as e:
        log_error("google_calendar", "Failed to create event", e)
        raise Exception(f"Failed to create calendar event: {str(e)}")


def create_assignment_block_event(
    access_token: str,
    assignment_title: str,
    start_time: datetime,
    end_time: datetime,
    due_date: datetime,
    refresh_token: str = None
) -> str:
    """
    Create a study block event for an assignment.
    Uses purple color (Grape = 3) for consistency.

    Args:
        access_token: Google OAuth access token
        assignment_title: Assignment name
        start_time: Study block start
        end_time: Study block end
        due_date: Assignment due date
        refresh_token: Google OAuth refresh token

    Returns:
        Event ID
    """
    days_until_due = (due_date.date() - start_time.date()).days

    title = f"📚 Work on {assignment_title}"
    description = f"Study session for {assignment_title}\nDue in {days_until_due} days ({due_date.strftime('%B %d, %Y')})"

    return create_calendar_event(
        access_token=access_token,
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        color_id="3",  # Grape (purple) for study blocks
        refresh_token=refresh_token
    )


def create_bus_event(
    access_token: str,
    direction: str,
    departure_time: datetime,
    arrival_time: datetime,
    departure_location: str,
    arrival_location: str,
    refresh_token: str = None
) -> str:
    """
    Create a bus commute event.
    Uses peacock blue (7) for commute events.

    Args:
        access_token: Google OAuth access token
        direction: "outbound" or "inbound"
        departure_time: Bus departure time
        arrival_time: Bus arrival time
        departure_location: Starting location
        arrival_location: Destination
        refresh_token: Google OAuth refresh token

    Returns:
        Event ID
    """
    if direction == "outbound":
        title = f"🚌 Bus to Campus"
        description = f"Westside bus: {departure_location} → {arrival_location}"
    else:
        title = f"🚌 Bus Home"
        description = f"Westside bus: {departure_location} → {arrival_location}"

    return create_calendar_event(
        access_token=access_token,
        title=title,
        start_time=departure_time,
        end_time=arrival_time,
        description=description,
        location=departure_location,
        color_id="7",  # Peacock blue for commute
        refresh_token=refresh_token
    )


def delete_calendar_event(
    access_token: str,
    event_id: str,
    refresh_token: str = None
) -> bool:
    """
    Delete an event from Google Calendar.

    Args:
        access_token: Google OAuth access token
        event_id: ID of event to delete
        refresh_token: Google OAuth refresh token

    Returns:
        True if successful
    """
    try:
        service = _build_calendar_service(access_token, refresh_token)
        service.events().delete(calendarId='primary', eventId=event_id).execute()

        log_info("google_calendar", "Deleted event", event_id=event_id)
        return True

    except Exception as e:
        log_error("google_calendar", "Failed to delete event", e)
        raise Exception(f"Failed to delete calendar event: {str(e)}")
