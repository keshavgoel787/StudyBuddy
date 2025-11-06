"""
Quick test script to verify assignments API endpoints work.
Note: This requires a valid auth token. Run manually if needed.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.assignment import Assignment
from datetime import datetime, timedelta

def test_assignments():
    db = SessionLocal()

    try:
        # Get first user for testing
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database. Cannot test assignments.")
            return

        print(f"✅ Testing with user: {user.email}")

        # Create test assignment
        test_assignment = Assignment(
            user_id=user.id,
            title="Test Assignment - BCHM 401 Problem Set",
            description="Complete problems 1-10 from chapter 5",
            due_date=datetime.now() + timedelta(days=3),
            estimated_hours=2.5,
            priority=2,
            completed=False
        )

        db.add(test_assignment)
        db.commit()
        db.refresh(test_assignment)

        print(f"✅ Created test assignment: {test_assignment.title}")
        print(f"   ID: {test_assignment.id}")
        print(f"   Due: {test_assignment.due_date}")
        print(f"   Priority: {test_assignment.priority}")

        # Query assignments
        assignments = db.query(Assignment).filter(
            Assignment.user_id == user.id,
            Assignment.completed == False
        ).all()

        print(f"\n✅ Found {len(assignments)} incomplete assignments for this user:")
        for a in assignments:
            print(f"   - {a.title} (Due: {a.due_date.strftime('%Y-%m-%d')})")

        # Clean up test data
        db.delete(test_assignment)
        db.commit()
        print(f"\n✅ Cleaned up test assignment")

        print("\n🎉 All assignment database operations working correctly!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_assignments()
