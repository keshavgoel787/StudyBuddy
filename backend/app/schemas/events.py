"""
Schemas for Google Calendar event creation.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    """Create a custom event in Google Calendar."""
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    color_id: Optional[str] = None  # 1-11


class EventCreateResponse(BaseModel):
    """Response after creating an event."""
    event_id: str
    message: str


class EventDeleteResponse(BaseModel):
    """Response after deleting an event."""
    success: bool
    message: str


class SyncAssignmentBlockRequest(BaseModel):
    """Request to sync assignment block to Google Calendar."""
    assignment_id: int
    start_time: datetime
    end_time: datetime


class SyncBusRequest(BaseModel):
    """Request to sync bus suggestion to Google Calendar."""
    direction: str  # "outbound" or "inbound"
    departure_time: datetime
    arrival_time: datetime


class AutoSyncPreferences(BaseModel):
    """Preferences for automatic syncing to Google Calendar."""
    auto_sync_assignments: bool = False  # Auto-create assignment block events
    auto_sync_buses: bool = False  # Auto-create bus events (separate from bus preferences)
