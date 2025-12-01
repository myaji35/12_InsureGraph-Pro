#!/bin/bash
# Apply database migration script
# Usage: ./apply_migration.sh <migration_file>

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if migration file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Migration file not specified${NC}"
    echo "Usage: ./apply_migration.sh <migration_file>"
    echo "Example: ./apply_migration.sh backend/alembic/versions/002_add_ingestion_jobs_table.sql"
    exit 1
fi

MIGRATION_FILE="$1"

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}Error: Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

# Load environment variables from .env if it exists
if [ -f "backend/.env" ]; then
    echo -e "${YELLOW}Loading environment variables from backend/.env${NC}"
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Check required environment variables
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ]; then
    echo -e "${RED}Error: Required database environment variables not set${NC}"
    echo "Please set: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD"
    exit 1
fi

# Build connection string
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB}"
DB_USER="${POSTGRES_USER}"

echo -e "${YELLOW}Applying migration: $MIGRATION_FILE${NC}"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo ""

# Apply migration using psql
PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f "$MIGRATION_FILE"

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Migration applied successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi
