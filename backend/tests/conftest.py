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
