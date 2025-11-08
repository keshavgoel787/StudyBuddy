from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Assignment(Base):
    """
    Assignment model for tracking user assignments/tasks.
    Each assignment belongs to a user and has a due date, priority, and completion status.
    """
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Assignment details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assignment_type = Column(String, nullable=True)  # e.g., "exam", "quiz", "lab report", "homework", "project", "essay", "presentation"
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    estimated_hours = Column(Float, default=1.0)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high

    # Status
    completed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
