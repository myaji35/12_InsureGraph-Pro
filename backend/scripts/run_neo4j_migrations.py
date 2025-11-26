#!/usr/bin/env python
"""
Neo4j migration runner script
"""
from neo4j import GraphDatabase
import os
import sys
from pathlib import Path


class Neo4jMigration:
    """Neo4j migration runner"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD")
            )
        )

    def close(self):
        """Close driver"""
        self.driver.close()

    def run_migration(self, migration_file):
        """Run a single migration file"""
        cypher = Path(migration_file).read_text()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in cypher.split(";") if s.strip()]

        with self.driver.session() as session:
            for statement in statements:
                if statement:
                    session.run(statement)

        print(f"✅ Migration {migration_file.name} completed successfully")


def main():
    """Main entry point"""
    print("🔌 Connecting to Neo4j")

    migration = Neo4jMigration()

    try:
        # Get migrations directory
        migrations_dir = Path(__file__).parent.parent / "migrations" / "neo4j"

        if not migrations_dir.exists():
            print(f"❌ Migrations directory not found: {migrations_dir}")
            sys.exit(1)

        # Get all migration files sorted
        migration_files = sorted(migrations_dir.glob("*.cypher"))

        if not migration_files:
            print("⚠️ No migration files found")
            sys.exit(0)

        print(f"📋 Found {len(migration_files)} migration(s)")

        for migration_file in migration_files:
            print(f"⏳ Running migration: {migration_file.name}")
            migration.run_migration(migration_file)

        print("\n✅ All migrations completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

    finally:
        migration.close()


if __name__ == "__main__":
    main()
