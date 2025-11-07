#!/usr/bin/env python3
"""
Quick script to test database connectivity.
Run this after waking up your Supabase database.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    sys.exit(1)

print("🔍 Testing database connection...")
print(f"📍 Database host: {DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'unknown'}")
print()

try:
    # Attempt to connect
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Test query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()

    print("✅ Database connection successful!")
    print(f"📊 PostgreSQL version: {version[0][:50]}...")

    # Check if tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()

    print(f"\n📋 Found {len(tables)} tables:")
    for table in tables:
        print(f"   - {table[0]}")

    cursor.close()
    conn.close()

    print("\n✅ All checks passed! Your database is ready.")

except psycopg2.OperationalError as e:
    print("❌ Database connection failed!")
    print(f"\nError: {str(e)}")
    print("\n💡 Possible solutions:")
    print("   1. Wake up your Supabase database at https://supabase.com/dashboard")
    print("   2. Check if DATABASE_URL in .env is correct")
    print("   3. Verify your internet connection")
    print("   4. Consider switching to local PostgreSQL for development")
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    sys.exit(1)
