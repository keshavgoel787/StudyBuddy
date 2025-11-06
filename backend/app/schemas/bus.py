from pydantic import BaseModel
from typing import Optional


class BusPreferencesUpdate(BaseModel):
    """Schema for updating user's bus preferences."""
    auto_create_events: Optional[bool] = None
    arrival_buffer_minutes: Optional[int] = None
    departure_buffer_minutes: Optional[int] = None


class BusPreferencesResponse(BaseModel):
    """Schema for bus preferences response."""
    auto_create_events: bool
    arrival_buffer_minutes: int
    departure_buffer_minutes: int
