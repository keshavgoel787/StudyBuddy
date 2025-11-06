from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CalendarEvent(BaseModel):
    id: str
    title: str
    location: Optional[str] = None
    start: datetime
    end: datetime


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


class Recommendations(BaseModel):
    lunch_slots: List[TimeSlot]
    study_slots: List[TimeSlot]
    commute_suggestion: Optional[CommuteSuggestion]
    bus_suggestions: Optional[dict] = None  # {"morning": BusSuggestion, "evening": BusSuggestion}
    summary: str


class DayPlanResponse(BaseModel):
    date: str
    events: List[CalendarEvent]
    free_blocks: List[FreeBlock]
    recommendations: Recommendations
