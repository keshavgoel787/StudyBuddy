from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, AssignmentResponse
from app.utils.auth_middleware import get_current_user
from app.utils.cache import invalidate_day_plan_cache

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=List[AssignmentResponse])
async def get_assignments(
    include_completed: bool = Query(False, description="Include completed assignments in results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all assignments for the current user.

    Query params:
    - include_completed: Set to true to include completed assignments (default: false)
    """
    try:
        query = db.query(Assignment).filter(Assignment.user_id == current_user.id)

        if not include_completed:
            query = query.filter(Assignment.completed == False)

        assignments = query.order_by(Assignment.due_date.asc()).all()
        return assignments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch assignments: {str(e)}")


@router.post("", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    assignment: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new assignment for the current user.
    """
    try:
        db_assignment = Assignment(
            user_id=current_user.id,
            title=assignment.title,
            description=assignment.description,
            due_date=assignment.due_date,
            estimated_hours=assignment.estimated_hours,
            priority=assignment.priority,
            completed=False
        )

        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)

        # Invalidate day plan cache since assignments changed
        invalidate_day_plan_cache(db, current_user.id)

        return db_assignment

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_update: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing assignment (partial updates allowed).
    Only the assignment owner can update it.
    """
    try:
        # Find assignment and verify ownership
        db_assignment = db.query(Assignment).filter(
            Assignment.id == assignment_id,
            Assignment.user_id == current_user.id
        ).first()

        if not db_assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Update only provided fields
        update_data = assignment_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_assignment, field, value)

        db.commit()
        db.refresh(db_assignment)

        # Invalidate day plan cache since assignments changed
        invalidate_day_plan_cache(db, current_user.id)

        return db_assignment

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update assignment: {str(e)}")


@router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an assignment.
    Only the assignment owner can delete it.
    """
    try:
        # Find assignment and verify ownership
        db_assignment = db.query(Assignment).filter(
            Assignment.id == assignment_id,
            Assignment.user_id == current_user.id
        ).first()

        if not db_assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        db.delete(db_assignment)
        db.commit()

        # Invalidate day plan cache since assignments changed
        invalidate_day_plan_cache(db, current_user.id)

        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete assignment: {str(e)}")
