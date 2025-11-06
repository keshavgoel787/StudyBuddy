from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from typing import Optional
from uuid import UUID


class AssignmentBase(BaseModel):
    """Base schema with shared fields for assignments."""
    title: str = Field(..., min_length=1, max_length=200, description="Assignment title")
    description: Optional[str] = Field(None, description="Detailed description of the assignment")
    due_date: datetime = Field(..., description="When the assignment is due (timezone-aware)")
    estimated_hours: float = Field(1.0, ge=0.1, le=100.0, description="Estimated hours to complete")
    priority: int = Field(1, ge=1, le=3, description="Priority level: 1=low, 2=medium, 3=high")


class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment."""
    pass


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment (all fields optional for PATCH)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0.1, le=100.0)
    priority: Optional[int] = Field(None, ge=1, le=3)
    completed: Optional[bool] = None


class AssignmentResponse(AssignmentBase):
    """Schema for assignment responses (includes all fields from DB)."""
    id: int
    user_id: UUID  # Will be serialized to string
    completed: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer('user_id')
    def serialize_user_id(self, user_id: UUID) -> str:
        """Convert UUID to string for JSON serialization."""
        return str(user_id)

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
