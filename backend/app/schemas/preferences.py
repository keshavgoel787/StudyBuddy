"""
Schemas for day preferences (mood/feeling).
"""

from pydantic import BaseModel
from datetime import date
from typing import Optional


class DayPreferencesCreate(BaseModel):
    """Create or update day preferences."""
    mood: str  # "chill" | "normal" | "grind"
    feeling: str  # "overwhelmed" | "okay" | "on_top"
    date: Optional[date] = None  # Defaults to today if not provided


class DayPreferencesResponse(BaseModel):
    """Response with user's day preferences."""
    mood: str
    feeling: str
    date: date
