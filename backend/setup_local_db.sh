#!/bin/bash
# Script to set up local PostgreSQL database for development

echo "🚀 Setting up local PostgreSQL database for StudyBuddy..."
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed."
    echo ""
    echo "📦 Install PostgreSQL:"
    echo "   macOS:   brew install postgresql@15"
    echo "   Ubuntu:  sudo apt install postgresql postgresql-contrib"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL is installed"

# Check if PostgreSQL service is running
if ! pg_isready &> /dev/null; then
    echo "⚠️  PostgreSQL service is not running"
    echo ""
    echo "🔧 Start PostgreSQL:"
    echo "   macOS:   brew services start postgresql@15"
    echo "   Ubuntu:  sudo systemctl start postgresql"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL service is running"
echo ""

# Create database and user
DB_NAME="studybuddy"
DB_USER="studybuddy_user"
DB_PASSWORD="local_dev_password_123"

echo "📊 Creating database and user..."

# Create user (ignore if exists)
psql postgres -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || echo "   User already exists, continuing..."

# Create database (ignore if exists)
psql postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || echo "   Database already exists, continuing..."

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" &>/dev/null

echo "✅ Database and user created"
echo ""

# Generate new DATABASE_URL
NEW_DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"

echo "📝 Your new local DATABASE_URL:"
echo ""
echo "   ${NEW_DB_URL}"
echo ""
echo "🔧 Next steps:"
echo ""
echo "   1. Update your backend/.env file:"
echo "      DATABASE_URL='${NEW_DB_URL}'"
echo ""
echo "   2. Run database migrations:"
echo "      cd backend"
echo "      alembic upgrade head"
echo ""
echo "   3. Test the connection:"
echo "      python test_db_connection.py"
echo ""
echo "   4. Start your backend server:"
echo "      uvicorn app.main:app --reload"
echo ""
echo "✅ Setup complete!"
