# Database Migrations

This directory contains database migration scripts for InsureGraph Pro.

## Structure

```
migrations/
├── postgresql/          # PostgreSQL migrations
│   ├── 001_initial_schema.sql
│   └── ...
├── neo4j/              # Neo4j migrations
│   ├── 001_initial_schema.cypher
│   └── ...
└── README.md           # This file
```

---

## PostgreSQL Migrations

### Prerequisites

- PostgreSQL 15+
- `psql` CLI tool
- Database created: `insuregraph`
- User created: `insuregraph_user`

### Running Migrations

**Manually with psql**:

```bash
# Set environment variables
export PGHOST="localhost"
export PGPORT="5432"
export PGDATABASE="insuregraph"
export PGUSER="insuregraph_user"
export PGPASSWORD="YOUR_PASSWORD"

# Run migration
psql -f postgresql/001_initial_schema.sql
```

**Using Python script** (recommended):

```bash
# Install dependencies
pip install psycopg2-binary

# Run migration
python scripts/run_pg_migrations.py
```

### Migration Script Template (Python)

```python
# scripts/run_pg_migrations.py
import psycopg2
import os
from pathlib import Path

def run_migration(migration_file):
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "insuregraph"),
        user=os.getenv("PGUSER", "insuregraph_user"),
        password=os.getenv("PGPASSWORD")
    )

    with conn.cursor() as cur:
        sql = Path(migration_file).read_text()
        cur.execute(sql)
        conn.commit()

    conn.close()
    print(f"Migration {migration_file} completed successfully")

if __name__ == "__main__":
    migrations_dir = Path("backend/migrations/postgresql")

    # Get all migration files sorted
    migration_files = sorted(migrations_dir.glob("*.sql"))

    for migration_file in migration_files:
        print(f"Running migration: {migration_file.name}")
        run_migration(migration_file)
```

---

## Neo4j Migrations

### Prerequisites

- Neo4j 5.x Enterprise Edition
- `cypher-shell` CLI tool
- Neo4j database started

### Running Migrations

**Manually with cypher-shell**:

```bash
# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="YOUR_PASSWORD"

# Run migration
cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD \
  -f neo4j/001_initial_schema.cypher
```

**Using Python script** (recommended):

```bash
# Install dependencies
pip install neo4j

# Run migration
python scripts/run_neo4j_migrations.py
```

### Migration Script Template (Python)

```python
# scripts/run_neo4j_migrations.py
from neo4j import GraphDatabase
import os
from pathlib import Path

class Neo4jMigration:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD")
            )
        )

    def close(self):
        self.driver.close()

    def run_migration(self, migration_file):
        cypher = Path(migration_file).read_text()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in cypher.split(";") if s.strip()]

        with self.driver.session() as session:
            for statement in statements:
                if statement:
                    session.run(statement)

        print(f"Migration {migration_file} completed successfully")

if __name__ == "__main__":
    migrations_dir = Path("backend/migrations/neo4j")

    # Get all migration files sorted
    migration_files = sorted(migrations_dir.glob("*.cypher"))

    migration = Neo4jMigration()

    try:
        for migration_file in migration_files:
            print(f"Running migration: {migration_file.name}")
            migration.run_migration(migration_file)
    finally:
        migration.close()
```

---

## Migration Naming Convention

Migrations should be named with a sequential number prefix:

```
001_initial_schema.sql
002_add_customer_notes.sql
003_add_policy_versions.sql
...
```

---

## Rollback Scripts

For each migration, create a corresponding rollback script:

### PostgreSQL Rollback Example

```sql
-- migrations/postgresql/rollback/001_initial_schema.sql

-- Drop tables in reverse order (respecting foreign keys)
DROP TABLE IF EXISTS rate_limits CASCADE;
DROP TABLE IF EXISTS system_config CASCADE;
DROP TABLE IF EXISTS daily_analytics CASCADE;
DROP TABLE IF EXISTS script_validations CASCADE;
DROP TABLE IF EXISTS expert_reviews CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS query_sources CASCADE;
DROP TABLE IF EXISTS query_logs CASCADE;
DROP TABLE IF EXISTS ingestion_job_stages CASCADE;
DROP TABLE IF EXISTS ingestion_jobs CASCADE;
DROP TABLE IF EXISTS customer_policies CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS user_permissions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS gas CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Drop extensions
DROP EXTENSION IF EXISTS "uuid-ossp";
DROP EXTENSION IF EXISTS "pgcrypto";

SELECT 'Rollback 001_initial_schema completed' AS status;
```

### Neo4j Rollback Example

```cypher
// migrations/neo4j/rollback/001_initial_schema.cypher

// Delete all seed data
MATCH (d:Disease) DELETE d;

// Drop vector index
DROP INDEX clause_embeddings IF EXISTS;

// Drop full-text indexes
DROP INDEX clause_text_search IF EXISTS;
DROP INDEX disease_search IF EXISTS;

// Drop regular indexes
DROP INDEX condition_type IF EXISTS;
DROP INDEX clause_article_num IF EXISTS;
DROP INDEX clause_product_id IF EXISTS;
DROP INDEX disease_severity IF EXISTS;
DROP INDEX disease_category IF EXISTS;
DROP INDEX disease_name_ko IF EXISTS;
DROP INDEX coverage_name IF EXISTS;
DROP INDEX coverage_type IF EXISTS;
DROP INDEX product_status IF EXISTS;
DROP INDEX product_launch_date IF EXISTS;
DROP INDEX product_insurer IF EXISTS;

// Drop constraints
DROP CONSTRAINT payment_rule_id IF EXISTS;
DROP CONSTRAINT exclusion_id IF EXISTS;
DROP CONSTRAINT clause_id IF EXISTS;
DROP CONSTRAINT condition_id IF EXISTS;
DROP CONSTRAINT disease_kcd IF EXISTS;
DROP CONSTRAINT disease_id IF EXISTS;
DROP CONSTRAINT coverage_id IF EXISTS;
DROP CONSTRAINT product_code IF EXISTS;
DROP CONSTRAINT product_id IF EXISTS;

RETURN "Rollback 001_initial_schema completed" AS status;
```

---

## Best Practices

### 1. Always Test Migrations

```bash
# Test on dev database first
export ENV=dev
python scripts/run_migrations.py

# Then staging
export ENV=staging
python scripts/run_migrations.py

# Finally production (with backup!)
export ENV=production
pg_dump insuregraph > backup_$(date +%Y%m%d_%H%M%S).sql
python scripts/run_migrations.py
```

### 2. Use Transactions (PostgreSQL)

Wrap migrations in transactions:

```sql
BEGIN;

-- Your migration SQL here

COMMIT;
-- ROLLBACK; -- if error occurs
```

### 3. Keep Migrations Idempotent

Use `IF NOT EXISTS` and `IF EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS new_table (...);
DROP TABLE IF EXISTS old_table;
```

```cypher
CREATE CONSTRAINT constraint_name IF NOT EXISTS ...;
DROP INDEX index_name IF EXISTS;
```

### 4. Document Breaking Changes

If a migration has breaking changes, document them:

```sql
-- BREAKING CHANGE: This migration renames the 'customer_name' column
-- to 'name_encrypted'. Update application code before deploying.

ALTER TABLE customers RENAME COLUMN customer_name TO name_encrypted;
```

### 5. Track Migration Status

Create a migrations table:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE
);

INSERT INTO schema_migrations (version) VALUES ('001_initial_schema');
```

---

## Troubleshooting

### PostgreSQL: Permission Denied

```bash
# Grant permissions to user
psql -U postgres -d insuregraph -c "GRANT ALL PRIVILEGES ON DATABASE insuregraph TO insuregraph_user;"
psql -U postgres -d insuregraph -c "GRANT ALL ON SCHEMA public TO insuregraph_user;"
```

### Neo4j: Connection Refused

```bash
# Check Neo4j is running
systemctl status neo4j

# Check credentials
cypher-shell -u neo4j -p your_password "RETURN 1;"
```

### Migration Failed Mid-way

**PostgreSQL**:
1. Check `schema_migrations` table for last successful migration
2. Run rollback script for failed migration
3. Fix migration script
4. Re-run migration

**Neo4j**:
1. No automatic transaction rollback for DDL
2. Manually run rollback cypher script
3. Fix migration script
4. Re-run migration

---

## GCP Cloud SQL Connection

For GCP Cloud SQL PostgreSQL:

```bash
# Via Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:5432 &

# Then connect
export PGHOST="127.0.0.1"
psql -f migrations/postgresql/001_initial_schema.sql
```

For GCP Compute Engine Neo4j:

```bash
# SSH tunnel
gcloud compute ssh insuregraph-neo4j \
  --zone=asia-northeast3-a \
  -- -L 7687:localhost:7687

# Then connect
export NEO4J_URI="bolt://localhost:7687"
cypher-shell -f migrations/neo4j/001_initial_schema.cypher
```

---

## Next Steps

After running initial migrations:

1. **Verify Schema**:
   ```bash
   # PostgreSQL
   psql -c "\dt"  # List tables
   psql -c "\d users"  # Describe table

   # Neo4j
   cypher-shell "SHOW CONSTRAINTS;"
   cypher-shell "SHOW INDEXES;"
   ```

2. **Run Tests**:
   ```bash
   pytest tests/test_database.py
   ```

3. **Seed Test Data** (optional):
   ```bash
   python scripts/seed_test_data.py
   ```

---

**Maintained By**: Backend Team
**Last Updated**: 2025-11-25
