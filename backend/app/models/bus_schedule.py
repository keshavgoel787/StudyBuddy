from sqlalchemy import Column, String, Time, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class Direction(str, enum.Enum):
    outbound = "outbound"  # To campus (Main & Murray → UDC or Union → Main & Murray)
    inbound = "inbound"    # From campus (UDC → Main & Murray or Main & Murray → Union)


class Route(str, enum.Enum):
    westside = "westside"  # Main & Murray ↔ UDC
    union = "union"        # Union ↔ Main & Murray


class BusSchedule(Base):
    """
    Stores bus schedules for multiple routes (Westside, Union, etc.).
    Each row represents one bus departure time.
    """
    __tablename__ = "bus_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route = Column(SQLEnum(Route), nullable=False, default=Route.westside)  # Route type
    direction = Column(SQLEnum(Direction), nullable=False)  # outbound or inbound

    # For Westside outbound: leaves Main & Murray → arrives UDC
    # For Westside inbound: leaves UDC → arrives Main & Murray
    # For Union outbound: leaves Union → arrives Main & Murray
    # For Union inbound: leaves Main & Murray → arrives Union
    departure_time = Column(Time, nullable=False)
    arrival_time = Column(Time, nullable=False)

    # Day of week (1=Monday, 5=Friday, 6=Saturday, 7=Sunday)
    day_of_week = Column(Integer, nullable=False)  # 1-7 for Mon-Sun

    # Travel duration in minutes (calculated from departure to arrival)
    duration_minutes = Column(Integer, nullable=False)

    # Optional: Mark special buses (late night, etc.)
    is_late_night = Column(Boolean, default=False)  # After 9 PM
