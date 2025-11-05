from sqlalchemy import Column, String, DateTime, JSON, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class DayPlan(Base):
    __tablename__ = "day_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)  # The date this plan is for
    events = Column(JSON, nullable=False)  # Cached events from Google Calendar
    free_blocks = Column(JSON, nullable=False)  # Calculated free blocks
    recommendations = Column(JSON, nullable=False)  # AI-generated recommendations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
