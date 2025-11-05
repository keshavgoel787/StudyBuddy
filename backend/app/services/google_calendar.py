from datetime import datetime, timedelta
from typing import List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.schemas.calendar import CalendarEvent


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
        # Create credentials object
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Not needed for API calls
            client_secret=None
        )

        # Build the Calendar API service
        service = build('calendar', 'v3', credentials=creds)

        # Get today's date range - use local time, not UTC
        # This prevents timezone issues where tomorrow's events show up today
        from datetime import date as date_type
        local_today = date_type.today()

        # Query events that START today (in local time)
        # Note: We don't append 'Z' to force UTC, which lets calendar times be interpreted correctly
        today_start = datetime(local_today.year, local_today.month, local_today.day, 0, 0, 0).isoformat() + 'Z'
        # Add one day for the end
        tomorrow = local_today.replace(day=local_today.day + 1) if local_today.day < 28 else local_today.replace(month=local_today.month + 1, day=1)
        tomorrow_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0).isoformat() + 'Z'
        today_end = tomorrow_start

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
        from datetime import date as date_type
        local_today = date_type.today()

        for event in events:
            # Handle both dateTime and date (all-day events)
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Parse datetime
            if 'T' in start:  # dateTime format
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:  # date format (all-day event)
                start_dt = datetime.fromisoformat(start + 'T00:00:00')
                end_dt = datetime.fromisoformat(end + 'T23:59:59')

            # Filter: only include events that start today (in the event's local timezone)
            event_date = start_dt.date()
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
