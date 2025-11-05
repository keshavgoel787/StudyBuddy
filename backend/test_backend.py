"""
Comprehensive test script to verify backend components
"""
from app.config import get_settings
from app.database import engine
from sqlalchemy import text
from datetime import datetime, time

def test_config():
    """Test that .env variables are loaded correctly"""
    print("=" * 60)
    print("1. Testing Configuration")
    print("=" * 60)
    settings = get_settings()

    print(f"✓ Database URL loaded: {settings.database_url[:30]}...")
    print(f"✓ Google Client ID loaded: {settings.google_client_id[:20]}...")
    print(f"✓ Gemini API Key loaded: {settings.gemini_api_key[:20]}...")
    print(f"✓ JWT Secret loaded: {settings.jwt_secret_key[:20]}...")
    print(f"✓ Frontend URL: {settings.frontend_url}")
    print()

def test_database():
    """Test database connection"""
    print("=" * 60)
    print("2. Testing Database Connection")
    print("=" * 60)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL!")
            print(f"  Version: {version[:60]}...")
            print()
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_models():
    """Test that models are importable"""
    print("=" * 60)
    print("3. Testing Database Models")
    print("=" * 60)
    try:
        from app.models import User, UserToken, NoteDocument, StudyMaterial
        print("✓ User model imported")
        print("✓ UserToken model imported")
        print("✓ NoteDocument model imported")
        print("✓ StudyMaterial model imported")
        print()
        return True
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False

def test_schemas():
    """Test that schemas are importable"""
    print("=" * 60)
    print("4. Testing Pydantic Schemas")
    print("=" * 60)
    try:
        from app.schemas.auth import UserResponse, TokenResponse
        from app.schemas.calendar import CalendarEvent, DayPlanResponse
        from app.schemas.notes import StudyMaterialResponse
        print("✓ Auth schemas imported")
        print("✓ Calendar schemas imported")
        print("✓ Notes schemas imported")
        print()
        return True
    except Exception as e:
        print(f"✗ Schema import failed: {e}")
        return False

def test_auth_utils():
    """Test JWT token creation and validation"""
    print("=" * 60)
    print("5. Testing Auth Utilities")
    print("=" * 60)
    try:
        from app.utils.auth_middleware import create_access_token
        import uuid

        # Create a test token
        test_user_id = str(uuid.uuid4())
        token = create_access_token(test_user_id)

        print(f"✓ JWT token created successfully")
        print(f"  Token: {token[:30]}...")

        # Decode and verify
        from jose import jwt
        from app.config import get_settings
        settings = get_settings()

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        print(f"✓ JWT token decoded successfully")
        print(f"  User ID in token: {payload['sub'][:20]}...")
        print()
        return True
    except Exception as e:
        print(f"✗ Auth utils test failed: {e}")
        return False

def test_time_utils():
    """Test time/free block calculation utilities"""
    print("=" * 60)
    print("6. Testing Time Utilities")
    print("=" * 60)
    try:
        from app.utils.time_utils import calculate_free_blocks, format_time_slot
        from app.schemas.calendar import CalendarEvent

        # Create test events
        test_events = [
            CalendarEvent(
                id="1",
                title="Morning Class",
                start=datetime(2025, 11, 8, 9, 0),
                end=datetime(2025, 11, 8, 10, 30)
            ),
            CalendarEvent(
                id="2",
                title="Afternoon Lab",
                start=datetime(2025, 11, 8, 14, 0),
                end=datetime(2025, 11, 8, 16, 0)
            )
        ]

        free_blocks = calculate_free_blocks(test_events)
        print(f"✓ Free block calculation works")
        print(f"  Found {len(free_blocks)} free blocks")

        for i, block in enumerate(free_blocks, 1):
            label = format_time_slot(block.start, block.end)
            print(f"  Block {i}: {label} ({block.duration_minutes} min)")

        print()
        return True
    except Exception as e:
        print(f"✗ Time utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "SchoolBuddy Backend - Component Tests" + " " * 10 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    test_config()
    results.append(("Database Connection", test_database()))
    results.append(("Models", test_models()))
    results.append(("Schemas", test_schemas()))
    results.append(("Auth Utilities", test_auth_utils()))
    results.append(("Time Utilities", test_time_utils()))

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:<10} {name}")

    print()
    all_passed = all(result[1] for result in results)

    if all_passed:
        print("🎉 All tests passed! Backend components are working.")
        print("Ready to continue building services and routes.")
    else:
        print("⚠️  Some tests failed. Fix the errors above.")

    print("=" * 60)
    print()
