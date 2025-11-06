from sqlalchemy import Column, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class UserBusPreferences(Base):
    """
    Stores user preferences for bus schedule integration.
    """
    __tablename__ = "user_bus_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Whether to automatically create Google Calendar events for suggested buses
    auto_create_events = Column(Boolean, default=False)

    # Buffer time before first class (in minutes) - how early they want to arrive
    # Default: 15 minutes before first class
    arrival_buffer_minutes = Column(Integer, default=15)

    # Buffer time after last class (in minutes) - how long after last class to leave
    # Default: 0 minutes (leave right after)
    departure_buffer_minutes = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
