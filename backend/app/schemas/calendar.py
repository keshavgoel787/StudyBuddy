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


class Recommendations(BaseModel):
    lunch_slots: List[TimeSlot]
    study_slots: List[TimeSlot]
    commute_suggestion: Optional[CommuteSuggestion]
    summary: str


class DayPlanResponse(BaseModel):
    date: str
    events: List[CalendarEvent]
    free_blocks: List[FreeBlock]
    recommendations: Recommendations
