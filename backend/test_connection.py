"""
Quick test script to verify database connection and config loading
"""
from app.config import get_settings
from app.database import engine
from sqlalchemy import text

def test_config():
    """Test that .env variables are loaded correctly"""
    print("Testing configuration...")
    settings = get_settings()

    print(f"✓ Database URL loaded: {settings.database_url[:30]}...")
    print(f"✓ Google Client ID loaded: {settings.google_client_id[:20]}...")
    print(f"✓ Gemini API Key loaded: {settings.gemini_api_key[:20]}...")
    print(f"✓ Frontend URL: {settings.frontend_url}")
    print()

def test_database():
    """Test database connection"""
    print("Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL!")
            print(f"  Version: {version[:50]}...")
            print()
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_models():
    """Test that models are importable"""
    print("Testing models...")
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
    print("Testing schemas...")
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

if __name__ == "__main__":
    print("=" * 60)
    print("SchoolBuddy Backend - Connection Test")
    print("=" * 60)
    print()

    test_config()
    db_ok = test_database()
    models_ok = test_models()
    schemas_ok = test_schemas()

    print("=" * 60)
    if db_ok and models_ok and schemas_ok:
        print("✓ All tests passed! Ready to continue.")
    else:
        print("✗ Some tests failed. Fix the errors above.")
    print("=" * 60)
