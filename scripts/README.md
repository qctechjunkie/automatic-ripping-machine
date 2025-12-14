# ARM Database Migration Scripts

This directory contains scripts for managing the ARM database during the FastAPI migration.

## Scripts

### add_database_indexes.py

Adds performance indexes to the existing ARM database to address slowdowns with large datasets (3000+ jobs).

**What it does:**
- Creates indexes on frequently queried columns (status, title, crc_id, etc.)
- Creates composite indexes for common query patterns
- Sets up SQLite FTS5 (Full-Text Search) for fast text searching
- Updates database statistics for query optimizer
- Creates automatic backup before making changes

**Usage:**

```bash
# Basic usage (uses database path from arm.yaml)
python scripts/add_database_indexes.py

# Specify custom database path
python scripts/add_database_indexes.py --db-path /path/to/arm.db

# Skip full-text search setup
python scripts/add_database_indexes.py --skip-fts

# Skip vacuum (faster, but won't reclaim space)
python scripts/add_database_indexes.py --skip-vacuum
```

**Safety:**
- Automatically creates a backup (arm.db.backup) before any changes
- Uses transactions - if anything fails, changes are rolled back
- Safe to run multiple times (skips existing indexes)

**Performance Impact:**
- Database queries will be significantly faster
- Sorting and filtering will be more efficient
- Text search will be near-instant (with FTS)
- The `/api/jobs` endpoint will load much faster

**When to run:**
- Before starting the FastAPI server for the first time
- After migrating from Flask to FastAPI
- If you notice slow query performance
- When upgrading ARM versions

## Future Scripts

Additional migration scripts will be added here as development progresses:
- `migrate_flask_to_fastapi.py` - Full migration helper
- `backup_database.py` - Automated backup utility
- `verify_database.py` - Database integrity checker
