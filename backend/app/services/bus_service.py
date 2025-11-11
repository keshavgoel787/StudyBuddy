"""
Service for finding optimal bus times based on user's schedule.
"""

from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.bus_schedule import BusSchedule, Direction, Route
from app.models.user_bus_preferences import UserBusPreferences
from app.schemas.calendar import CalendarEvent


class BusSuggestion:
    """Represents a suggested bus to take."""

    def __init__(
        self,
        direction: Direction,
        departure_time: time,
        arrival_time: time,
        reason: str,
        is_late_night: bool = False
    ):
        self.direction = direction
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.reason = reason
        self.is_late_night = is_late_night

    def to_dict(self, date: datetime.date) -> dict:
        """Convert to dictionary for API response."""
        # Combine date with time to create full datetime
        departure_dt = datetime.combine(date, self.departure_time)
        arrival_dt = datetime.combine(date, self.arrival_time)

        # Handle overnight buses (arrival next day)
        if self.arrival_time < self.departure_time:
            arrival_dt += timedelta(days=1)

        return {
            "direction": self.direction.value,
            "departure_time": departure_dt.isoformat(),
            "arrival_time": arrival_dt.isoformat(),
            "departure_label": self.departure_time.strftime("%I:%M %p"),
            "arrival_label": self.arrival_time.strftime("%I:%M %p"),
            "reason": self.reason,
            "is_late_night": self.is_late_night
        }


def find_bus_to_campus(
    db: Session,
    target_arrival: datetime,
    buffer_minutes: int = 15
) -> Optional[BusSuggestion]:
    """
    Find the best outbound bus to get to campus before target_arrival.

    Args:
        db: Database session
        target_arrival: When the user needs to be at campus (e.g., first class time)
        buffer_minutes: How many minutes before target to arrive (default 15)

    Returns:
        BusSuggestion for the optimal bus, or None if no suitable bus found
    """
    # Get day of week (1=Monday, 7=Sunday)
    day_of_week = target_arrival.isoweekday()

    # Only run Monday-Friday
    if day_of_week > 5:
        return None

    # Calculate the latest acceptable arrival time (as datetime for timezone consistency)
    desired_arrival_dt = target_arrival - timedelta(minutes=buffer_minutes)
    desired_arrival_time = desired_arrival_dt.time()

    # Query outbound buses for this day
    buses = db.query(BusSchedule).filter(
        BusSchedule.direction == Direction.outbound,
        BusSchedule.day_of_week == day_of_week,
        BusSchedule.arrival_time <= desired_arrival_time
    ).order_by(BusSchedule.arrival_time.desc()).all()

    if not buses:
        return None

    # Get the last bus that arrives before desired time (closest to target)
    best_bus = buses[0]

    # Calculate actual arrival time relative to target
    # Make sure both datetimes have the same timezone awareness
    arrival_dt = datetime.combine(target_arrival.date(), best_bus.arrival_time)

    # If target_arrival is timezone-aware, make arrival_dt timezone-aware too
    if target_arrival.tzinfo is not None:
        # Use the same timezone as target_arrival
        arrival_dt = arrival_dt.replace(tzinfo=target_arrival.tzinfo)

    minutes_early = int((target_arrival - arrival_dt).total_seconds() / 60)

    reason = f"Arrives at campus {minutes_early} min before first class"

    return BusSuggestion(
        direction=Direction.outbound,
        departure_time=best_bus.departure_time,
        arrival_time=best_bus.arrival_time,
        reason=reason,
        is_late_night=best_bus.is_late_night
    )


def find_bus_from_campus(
    db: Session,
    earliest_departure: datetime,
    buffer_minutes: int = 0
) -> Optional[BusSuggestion]:
    """
    Find the best inbound bus to leave campus after earliest_departure.

    Args:
        db: Database session
        earliest_departure: Earliest time user can leave campus (e.g., last class end time)
        buffer_minutes: How many minutes after to wait before leaving (default 0)

    Returns:
        BusSuggestion for the optimal bus, or None if no suitable bus found
    """
    # Get day of week (1=Monday, 7=Sunday)
    day_of_week = earliest_departure.isoweekday()

    # Only run Monday-Friday
    if day_of_week > 5:
        return None

    # Calculate the earliest acceptable departure time (as datetime for timezone consistency)
    desired_departure_dt = earliest_departure + timedelta(minutes=buffer_minutes)
    desired_departure_time = desired_departure_dt.time()

    # Query inbound buses for this day
    buses = db.query(BusSchedule).filter(
        BusSchedule.direction == Direction.inbound,
        BusSchedule.day_of_week == day_of_week,
        BusSchedule.departure_time >= desired_departure_time
    ).order_by(BusSchedule.departure_time.asc()).all()

    if not buses:
        return None

    # Get the first bus that departs after desired time (soonest after last class)
    best_bus = buses[0]

    # Calculate wait time
    # Make sure both datetimes have the same timezone awareness
    departure_dt = datetime.combine(earliest_departure.date(), best_bus.departure_time)

    # If earliest_departure is timezone-aware, make departure_dt timezone-aware too
    if earliest_departure.tzinfo is not None:
        # Use the same timezone as earliest_departure
        departure_dt = departure_dt.replace(tzinfo=earliest_departure.tzinfo)

    wait_minutes = int((departure_dt - earliest_departure).total_seconds() / 60)

    reason = f"Departs {wait_minutes} min after last class ends"

    return BusSuggestion(
        direction=Direction.inbound,
        departure_time=best_bus.departure_time,
        arrival_time=best_bus.arrival_time,
        reason=reason,
        is_late_night=best_bus.is_late_night
    )


def get_bus_suggestions_for_day(
    db: Session,
    user_id: str,
    date: datetime.date,
    events: List[CalendarEvent]
) -> Tuple[Optional[BusSuggestion], Optional[BusSuggestion]]:
    """
    Get bus suggestions for a given day based on user's calendar events.

    Args:
        db: Database session
        user_id: User's UUID
        date: The date to get suggestions for
        events: List of calendar events for the day

    Returns:
        Tuple of (morning_bus, evening_bus) suggestions, either can be None
    """
    # Get user's bus preferences (or use defaults)
    prefs = db.query(UserBusPreferences).filter(
        UserBusPreferences.user_id == user_id
    ).first()

    arrival_buffer = prefs.arrival_buffer_minutes if prefs else 15
    departure_buffer = prefs.departure_buffer_minutes if prefs else 0

    # Filter events to only those on campus
    # Strategy: Include events with physical locations, exclude remote/online events
    campus_location_keywords = ["udc", "campus", "student hold", "university", "building", "room"]
    remote_indicators = ["zoom.us", "http://", "https://", "meet.google", "teams.microsoft", "online", "virtual", "remote"]
    remote_title_keywords = ["online", "virtual", "zoom", "remote"]

    campus_events = []
    for e in events:
        # Check if title suggests it's remote
        title_is_remote = any(keyword in e.title.lower() for keyword in remote_title_keywords)

        # Check if event is explicitly remote/online via location
        location_is_remote = False
        if e.location:
            location_lower = e.location.lower()
            location_is_remote = any(indicator in location_lower for indicator in remote_indicators)

        is_remote = location_is_remote or title_is_remote

        # Skip remote events entirely
        if is_remote:
            continue

        # Check if event has explicit campus location
        has_campus_location = e.location and any(loc in e.location.lower() for loc in campus_location_keywords)

        # If event has ANY location (not None/empty) and it's not remote, assume it's on campus
        has_physical_location = e.location and len(e.location.strip()) > 0

        # Check if title explicitly mentions campus location
        title_mentions_campus = any(loc in e.title.lower() for loc in campus_location_keywords)

        # Include if:
        # 1. Has campus location keyword in location field, OR
        # 2. Has ANY physical location (room number, building, etc), OR
        # 3. Title mentions campus location
        if has_campus_location or has_physical_location or title_mentions_campus:
            campus_events.append(e)

    # If no campus events, no bus suggestions needed
    if not campus_events:
        return None, None

    # Find first and last campus events
    first_event = min(campus_events, key=lambda e: e.start)
    last_event = max(campus_events, key=lambda e: e.end)

    # Find morning bus (to arrive before first class)
    morning_bus = find_bus_to_campus(db, first_event.start, arrival_buffer)

    # Find evening bus (to leave after last class)
    evening_bus = find_bus_from_campus(db, last_event.end, departure_buffer)

    return morning_bus, evening_bus


def get_all_buses_for_day(
    db: Session,
    date: datetime.date,
    events: Optional[List[CalendarEvent]] = None,
    filter_by_schedule: bool = True
) -> dict:
    """
    Get all bus schedules for a specific day, optionally filtered by calendar events.

    Args:
        db: Database session
        date: The date to get buses for
        events: Optional list of calendar events to filter buses against
        filter_by_schedule: If True, filter buses based on events

    Returns:
        Dictionary with 'outbound' and 'inbound' lists of bus times
    """
    day_of_week = date.isoweekday()

    # Only Monday-Friday
    if day_of_week > 5:
        return {"outbound": [], "inbound": []}

    # Get all outbound buses for both routes
    westside_outbound = db.query(BusSchedule).filter(
        BusSchedule.route == Route.westside,
        BusSchedule.direction == Direction.outbound,
        BusSchedule.day_of_week == day_of_week
    ).order_by(BusSchedule.departure_time).all()

    union_outbound = db.query(BusSchedule).filter(
        BusSchedule.route == Route.union,
        BusSchedule.direction == Direction.outbound,
        BusSchedule.day_of_week == day_of_week
    ).order_by(BusSchedule.departure_time).all()

    # Get all inbound buses for both routes
    westside_inbound = db.query(BusSchedule).filter(
        BusSchedule.route == Route.westside,
        BusSchedule.direction == Direction.inbound,
        BusSchedule.day_of_week == day_of_week
    ).order_by(BusSchedule.departure_time).all()

    union_inbound = db.query(BusSchedule).filter(
        BusSchedule.route == Route.union,
        BusSchedule.direction == Direction.inbound,
        BusSchedule.day_of_week == day_of_week
    ).order_by(BusSchedule.departure_time).all()

    def bus_to_dict(bus: BusSchedule) -> dict:
        """Convert bus schedule to dict with full datetime strings."""
        departure_dt = datetime.combine(date, bus.departure_time)
        arrival_dt = datetime.combine(date, bus.arrival_time)

        # Handle overnight buses (arrival next day)
        if bus.arrival_time < bus.departure_time:
            arrival_dt += timedelta(days=1)

        return {
            "route": bus.route.value,
            "direction": bus.direction.value,
            "departure_time": departure_dt.isoformat(),
            "arrival_time": arrival_dt.isoformat(),
            "departure_label": bus.departure_time.strftime("%I:%M %p"),
            "arrival_label": bus.arrival_time.strftime("%I:%M %p"),
            "is_late_night": bus.is_late_night
        }

    # Filter buses based on schedule if events provided
    if filter_by_schedule and events:
        # Filter events to only those on campus
        campus_location_keywords = ["udc", "campus", "student hold", "university", "building", "room"]
        remote_indicators = ["zoom.us", "http://", "https://", "meet.google", "teams.microsoft", "online", "virtual", "remote"]
        remote_title_keywords = ["online", "virtual", "zoom", "remote"]

        campus_events = []
        for e in events:
            # Check if title suggests it's remote
            title_is_remote = any(keyword in e.title.lower() for keyword in remote_title_keywords)

            # Check if event is explicitly remote/online via location
            location_is_remote = False
            if e.location:
                location_lower = e.location.lower()
                location_is_remote = any(indicator in location_lower for indicator in remote_indicators)

            is_remote = location_is_remote or title_is_remote

            # Skip remote events entirely
            if is_remote:
                continue

            # Check if event has explicit campus location
            has_campus_location = e.location and any(loc in e.location.lower() for loc in campus_location_keywords)

            # If event has ANY location (not None/empty) and it's not remote, assume it's on campus
            has_physical_location = e.location and len(e.location.strip()) > 0

            # Check if title explicitly mentions campus location
            title_mentions_campus = any(loc in e.title.lower() for loc in campus_location_keywords)

            # Include if:
            # 1. Has campus location keyword in location field, OR
            # 2. Has ANY physical location (room number, building, etc), OR
            # 3. Title mentions campus location
            if has_campus_location or has_physical_location or title_mentions_campus:
                campus_events.append(e)

        def filter_buses(buses, first_event_time=None, last_event_time=None, is_outbound=True):
            """Filter buses based on event schedule"""
            filtered = []

            for bus in buses:
                # For outbound: must arrive before first event
                # For inbound: must depart after last event
                if is_outbound and first_event_time:
                    if bus.arrival_time > (datetime.combine(date, first_event_time) - timedelta(minutes=5)).time():
                        continue
                elif not is_outbound and last_event_time:
                    if bus.departure_time < last_event_time:
                        continue

                # Check if bus ride conflicts with any event
                bus_departure_dt = datetime.combine(date, bus.departure_time)
                bus_arrival_dt = datetime.combine(date, bus.arrival_time)

                # Handle overnight buses
                if bus.arrival_time < bus.departure_time:
                    bus_arrival_dt += timedelta(days=1)

                # Check for conflicts with any event
                conflicts = False
                for event in campus_events:
                    event_start = event.start
                    event_end = event.end

                    # Make sure all datetimes are comparable (timezone-aware)
                    if event_start.tzinfo is not None:
                        bus_departure_dt = bus_departure_dt.replace(tzinfo=event_start.tzinfo)
                        bus_arrival_dt = bus_arrival_dt.replace(tzinfo=event_start.tzinfo)

                    # Check if bus ride overlaps with event
                    if bus_departure_dt < event_end and bus_arrival_dt > event_start:
                        conflicts = True
                        break

                if not conflicts:
                    filtered.append(bus)

            return filtered

        # Apply filtering if campus events exist
        if campus_events:
            first_event = min(campus_events, key=lambda e: e.start)
            last_event = max(campus_events, key=lambda e: e.end)

            westside_outbound = filter_buses(westside_outbound, first_event_time=first_event.start.time(), is_outbound=True)
            union_outbound = filter_buses(union_outbound, first_event_time=first_event.start.time(), is_outbound=True)
            westside_inbound = filter_buses(westside_inbound, last_event_time=last_event.end.time(), is_outbound=False)
            union_inbound = filter_buses(union_inbound, last_event_time=last_event.end.time(), is_outbound=False)

    return {
        "westside": {
            "to_campus": [bus_to_dict(bus) for bus in westside_outbound],  # Main & Murray → UDC
            "from_campus": [bus_to_dict(bus) for bus in westside_inbound]  # UDC → Main & Murray
        },
        "union": {
            "to_main_murray": [bus_to_dict(bus) for bus in union_outbound],  # Union → Main & Murray
            "from_main_murray": [bus_to_dict(bus) for bus in union_inbound]  # Main & Murray → Union
        }
    }
