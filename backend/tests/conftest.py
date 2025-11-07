"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.user_token import UserToken
from app.models.note_document import NoteDocument
from app.models.study_material import StudyMaterial
from app.models.day_plan import DayPlan
from app.models.assignment import Assignment
from app.models.bus_schedule import BusSchedule, Direction
from app.models.day_preferences import DayPreferences, MoodType, FeelingType


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session, test_user):
    """Create a test client with database dependency override."""
    from app.utils.auth_middleware import get_current_user

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        """Override auth to always return test user"""
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Disable rate limiting for tests
    app.state.limiter.enabled = False

    with TestClient(app) as test_client:
        yield test_client

    # Re-enable rate limiting after tests
    app.state.limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        google_id="test_google_123",
        email="test@example.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(db_session, test_user):
    """Create a test user token."""
    from datetime import datetime, timedelta

    token = UserToken(
        user_id=test_user.id,
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expiry=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token


@pytest.fixture
def test_note_document(db_session, test_user):
    """Create a test note document."""
    note = NoteDocument(
        user_id=test_user.id,
        title="Test Biochemistry Notes",
        extracted_text="Enzymes are biological catalysts that speed up reactions."
    )
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)
    return note


@pytest.fixture
def test_study_material(db_session, test_note_document):
    """Create test study material."""
    material = StudyMaterial(
        note_document_id=test_note_document.id,
        summary_short="Enzymes catalyze reactions.",
        summary_detailed="Enzymes are proteins that act as biological catalysts.",
        flashcards=[
            {"question": "What are enzymes?", "answer": "Biological catalysts"}
        ],
        practice_questions=[
            {
                "question": "What do enzymes do?",
                "options": ["Speed up reactions", "Slow down reactions", "Stop reactions", "None"],
                "correct_index": 0,
                "explanation": "Enzymes speed up chemical reactions."
            }
        ]
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def auth_headers(test_user):
    """Create mock auth headers for testing protected endpoints."""
    # In real implementation, you'd generate a proper JWT
    # For now, we'll mock the auth middleware
    return {"Authorization": f"Bearer test_token_{test_user.id}"}


@pytest.fixture
def test_assignment(db_session, test_user):
    """Create a test assignment."""
    from datetime import datetime, timedelta, timezone

    assignment = Assignment(
        user_id=test_user.id,
        title="Physics Homework",
        description="Chapter 5 problems",
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
        estimated_hours=2.0,
        priority=2,
        completed=False
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


@pytest.fixture
def test_assignments(db_session, test_user):
    """Create multiple test assignments."""
    from datetime import datetime, timedelta, timezone

    assignments = [
        Assignment(
            user_id=test_user.id,
            title="Physics Homework",
            due_date=datetime.now(timezone.utc) + timedelta(days=2),
            estimated_hours=2.0,
            priority=3,
            completed=False
        ),
        Assignment(
            user_id=test_user.id,
            title="Chemistry Lab Report",
            due_date=datetime.now(timezone.utc) + timedelta(days=5),
            estimated_hours=3.0,
            priority=2,
            completed=False
        ),
        Assignment(
            user_id=test_user.id,
            title="Biology Reading",
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            estimated_hours=1.5,
            priority=1,
            completed=False
        ),
    ]

    for assignment in assignments:
        db_session.add(assignment)
    db_session.commit()

    for assignment in assignments:
        db_session.refresh(assignment)

    return assignments


@pytest.fixture
def test_calendar_events():
    """Create test calendar events."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from app.schemas.calendar import CalendarEvent

    est = ZoneInfo("America/New_York")
    today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)

    return [
        CalendarEvent(
            id="event1",
            title="Morning Lecture",
            start=today.replace(hour=9),
            end=today.replace(hour=10, minute=30),
            event_type="calendar"
        ),
        CalendarEvent(
            id="event2",
            title="Lab Session",
            start=today.replace(hour=14),
            end=today.replace(hour=16),
            event_type="calendar"
        ),
    ]


@pytest.fixture
def test_day_preferences(db_session, test_user):
    """Create test day preferences."""
    from datetime import date

    prefs = DayPreferences(
        user_id=test_user.id,
        date=date.today(),
        mood=MoodType.normal,
        feeling=FeelingType.okay
    )
    db_session.add(prefs)
    db_session.commit()
    db_session.refresh(prefs)
    return prefs
