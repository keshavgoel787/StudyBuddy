from sqlalchemy import Column, String, Time, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class Direction(str, enum.Enum):
    outbound = "outbound"  # Main & Murray → UDC
    inbound = "inbound"    # UDC → Main & Murray


class BusSchedule(Base):
    """
    Stores the Westside (WS) bus schedule.
    Each row represents one bus departure time.
    """
    __tablename__ = "bus_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    direction = Column(SQLEnum(Direction), nullable=False)  # outbound or inbound

    # For outbound: leaves Main & Murray
    # For inbound: leaves UDC
    departure_time = Column(Time, nullable=False)

    # For outbound: arrives at UDC
    # For inbound: arrives at Main & Murray
    arrival_time = Column(Time, nullable=False)

    # Day of week (1=Monday, 5=Friday) - currently all are Mon-Fri
    day_of_week = Column(Integer, nullable=False)  # 1-5 for Mon-Fri

    # Travel duration in minutes (calculated from departure to arrival)
    duration_minutes = Column(Integer, nullable=False)

    # Optional: Mark special buses (late night, etc.)
    is_late_night = Column(Boolean, default=False)  # After 9 PM
