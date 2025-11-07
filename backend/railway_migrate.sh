#!/bin/bash
# Railway migration script
# This runs migrations only when DATABASE_URL is available

set -e  # Exit on error

echo "🔍 Checking DATABASE_URL..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is not set. Skipping migrations."
    exit 1
fi

echo "✅ DATABASE_URL is set"
echo "🚀 Running database migrations..."

# Run Alembic migrations
alembic upgrade head

echo "✅ Migrations completed successfully"
