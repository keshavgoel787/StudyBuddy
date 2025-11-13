from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CalendarEvent(BaseModel):
    id: str
    title: str
    location: Optional[str] = None
    start: datetime
    end: datetime
    description: Optional[str] = None
    event_type: str = "calendar"  # "calendar" | "commute" | "assignment"
    color_id: Optional[str] = None  # Google Calendar color ID (1-11)


class FreeBlock(BaseModel):
    start: datetime
    end: datetime
    duration_minutes: int


class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    label: str  # e.g., "12:15 PM - 1:00 PM"


class CommuteSuggestion(BaseModel):
    leave_by: datetime
    leave_by_label: str  # e.g., "7:15 PM"
    reason: str


class BusSuggestion(BaseModel):
    direction: str  # "outbound" or "inbound"
    departure_time: datetime
    arrival_time: datetime
    departure_label: str  # e.g., "7:30 AM"
    arrival_label: str    # e.g., "7:40 AM"
    reason: str
    is_late_night: bool = False
    minutes_until_leave: Optional[int] = None  # Minutes from now until departure
    backup_bus: Optional['BusSuggestion'] = None  # Next available bus if missed


class Recommendations(BaseModel):
    lunch_slots: List[TimeSlot]
    study_slots: List[TimeSlot]
    commute_suggestion: Optional[CommuteSuggestion]
    bus_suggestions: Optional[dict] = None  # {"morning": BusSuggestion, "evening": BusSuggestion}
    summary: str


class DayPreferences(BaseModel):
    mood: str  # "chill" | "normal" | "grind"
    feeling: str  # "overwhelmed" | "okay" | "on_top"


class AssignmentGroup(BaseModel):
    """Grouped assignments for display."""
    title: str  # e.g., "Today's Focus for Dippi ✨"
    assignments: List[dict]  # Assignment objects with additional display fields


class FocusAssignment(BaseModel):
    """Top priority assignments for today."""
    id: int
    title: str
    due_in_days: int
    sessions_today: int  # Number of study sessions scheduled today
    sessions_total: int  # Total sessions needed (estimated_hours / block_size)


class UpNext(BaseModel):
    """Next upcoming event/task."""
    type: str  # "event" | "free" | "focus"
    title: str
    start_time: datetime
    start_label: str  # e.g., "2:30 PM"
    minutes_until: int


class TomorrowPreview(BaseModel):
    """Summary of tomorrow's schedule."""
    date: str
    total_events: int
    first_event_time: Optional[str] = None
    busy_hours: float
    study_hours: float


class WeeklyLoadDay(BaseModel):
    """Single day in weekly overview."""
    date: str
    day_name: str  # e.g., "Mon", "Tue"
    busy_hours: float
    study_hours: float
    total_events: int


class WeeklyLoad(BaseModel):
    """7-day overview of workload."""
    days: List[WeeklyLoadDay]
    total_busy_hours: float
    total_study_hours: float
    average_hours_per_day: float


class DayPlanResponse(BaseModel):
    date: str
    events: List[CalendarEvent]
    free_blocks: List[FreeBlock]
    recommendations: Recommendations
    preferences: Optional[DayPreferences] = None  # User's mood/feeling
    assignment_groups: Optional[List[AssignmentGroup]] = None
    focus_assignments: Optional[List[FocusAssignment]] = None
    up_next: Optional[UpNext] = None
    tomorrow_preview: Optional[TomorrowPreview] = None
