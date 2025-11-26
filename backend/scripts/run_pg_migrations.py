#!/usr/bin/env python
"""
PostgreSQL migration runner script
"""
import psycopg2
import os
import sys
from pathlib import Path


def run_migration(migration_file, conn):
    """Run a single migration file"""
    with conn.cursor() as cur:
        sql = Path(migration_file).read_text()
        cur.execute(sql)
        conn.commit()
    print(f"✅ Migration {migration_file.name} completed successfully")


def main():
    """Main entry point"""
    # Get database connection details from environment
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "insuregraph"),
        user=os.getenv("POSTGRES_USER", "insuregraph_user"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

    print("🔌 Connected to PostgreSQL")

    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations" / "postgresql"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Get all migration files sorted
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("⚠️ No migration files found")
        sys.exit(0)

    print(f"📋 Found {len(migration_files)} migration(s)")

    try:
        for migration_file in migration_files:
            print(f"⏳ Running migration: {migration_file.name}")
            run_migration(migration_file, conn)

        print("\n✅ All migrations completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
