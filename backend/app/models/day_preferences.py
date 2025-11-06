"""
Day preferences model for storing user's daily mood and feeling.
"""

from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class MoodType(str, enum.Enum):
    """User's energy/motivation level for the day."""
    chill = "chill"      # Low intensity, prefer lighter schedule
    normal = "normal"    # Balanced schedule
    grind = "grind"      # High intensity, can handle more work


class FeelingType(str, enum.Enum):
    """User's stress/capacity level for the day."""
    overwhelmed = "overwhelmed"  # Feeling stressed, need lighter load
    okay = "okay"                # Normal capacity
    on_top = "on_top"            # Feeling great, can handle more


class DayPreferences(Base):
    """
    Stores user's mood and feeling preferences for a specific day.
    Used by planning agent to adjust scheduling intensity.
    """
    __tablename__ = "day_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # User's mood and feeling for the day
    mood = Column(SQLEnum(MoodType), nullable=False, default=MoodType.normal)
    feeling = Column(SQLEnum(FeelingType), nullable=False, default=FeelingType.okay)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
