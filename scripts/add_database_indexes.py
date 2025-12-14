#!/usr/bin/env python3
"""
Database Index Migration Script
Adds performance indexes to existing ARM database

This script addresses the performance issue noted in arm/ui/database/database.py:38
where loading 3000+ jobs causes slowdowns.

Usage:
    python scripts/add_database_indexes.py [--db-path PATH]

Options:
    --db-path PATH    Path to SQLite database (default: reads from arm.yaml)
"""
import argparse
import sys
import sqlite3
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import arm.config.config as cfg
    default_db = cfg.arm_config.get('DBFILE', 'arm.db')
except Exception as e:
    print(f"Warning: Could not load ARM config: {e}")
    default_db = "arm.db"


# ============================================================================
# Index Definitions
# ============================================================================

INDEXES = [
    # Single column indexes for filtering
    ("idx_job_status", "job", "status"),
    ("idx_job_title", "job", "title"),
    ("idx_job_crc_id", "job", "crc_id"),
    ("idx_job_created", "job", "start_time"),
    ("idx_job_video_type", "job", "video_type"),
    ("idx_job_disctype", "job", "disctype"),
    ("idx_job_year", "job", "year"),

    # Composite indexes for common queries
    ("idx_job_status_created", "job", "status, start_time DESC"),
    ("idx_job_status_video_type", "job", "status, video_type"),
    ("idx_job_title_year", "job", "title, year"),
    ("idx_job_video_type_year", "job", "video_type, year"),

    # Indexes for other tables
    ("idx_track_job_id", "track", "job_id"),
    ("idx_config_job_id", "config", "job_id"),
]

# Full-text search setup
FTS_SETUP = """
-- Create FTS5 virtual table for fast text search
CREATE VIRTUAL TABLE IF NOT EXISTS job_fts USING fts5(
    job_id UNINDEXED,
    title,
    year,
    label,
    content='job',
    content_rowid='job_id'
);

-- Populate FTS table with existing data
INSERT OR IGNORE INTO job_fts(job_id, title, year, label)
SELECT job_id, title, year, label FROM job;

-- Triggers to keep FTS in sync with job table
DROP TRIGGER IF EXISTS job_fts_ai;
CREATE TRIGGER job_fts_ai AFTER INSERT ON job BEGIN
    INSERT INTO job_fts(job_id, title, year, label)
    VALUES (new.job_id, new.title, new.year, new.label);
END;

DROP TRIGGER IF EXISTS job_fts_ad;
CREATE TRIGGER job_fts_ad AFTER DELETE ON job BEGIN
    DELETE FROM job_fts WHERE job_id = old.job_id;
END;

DROP TRIGGER IF EXISTS job_fts_au;
CREATE TRIGGER job_fts_au AFTER UPDATE ON job BEGIN
    UPDATE job_fts SET
        title = new.title,
        year = new.year,
        label = new.label
    WHERE job_id = new.job_id;
END;
"""


# ============================================================================
# Migration Functions
# ============================================================================

def check_index_exists(cursor: sqlite3.Cursor, index_name: str) -> bool:
    """
    Check if an index already exists.

    Args:
        cursor: Database cursor
        index_name: Name of the index

    Returns:
        bool: True if index exists
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cursor.fetchone() is not None


def create_index(cursor: sqlite3.Cursor, index_def: Tuple[str, str, str]) -> bool:
    """
    Create a single index.

    Args:
        cursor: Database cursor
        index_def: Tuple of (index_name, table_name, columns)

    Returns:
        bool: True if created, False if already exists
    """
    index_name, table_name, columns = index_def

    if check_index_exists(cursor, index_name):
        print(f"  ⏭  {index_name} already exists")
        return False

    try:
        sql = f"CREATE INDEX {index_name} ON {table_name}({columns})"
        cursor.execute(sql)
        print(f"  ✓ Created {index_name} on {table_name}({columns})")
        return True
    except sqlite3.Error as e:
        print(f"  ✗ Failed to create {index_name}: {e}")
        return False


def setup_full_text_search(cursor: sqlite3.Cursor) -> bool:
    """
    Set up full-text search (FTS5) on job table.

    Args:
        cursor: Database cursor

    Returns:
        bool: True if successful
    """
    # Check if FTS table already exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='job_fts'"
    )
    if cursor.fetchone():
        print("  ⏭  Full-text search already configured")
        return False

    try:
        # Execute FTS setup (multiple statements)
        cursor.executescript(FTS_SETUP)
        print("  ✓ Full-text search configured")
        return True
    except sqlite3.Error as e:
        print(f"  ✗ Failed to setup full-text search: {e}")
        return False


def analyze_database(cursor: sqlite3.Cursor):
    """
    Run ANALYZE to update query planner statistics.

    Args:
        cursor: Database cursor
    """
    try:
        cursor.execute("ANALYZE")
        print("  ✓ Database statistics updated (ANALYZE)")
    except sqlite3.Error as e:
        print(f"  ✗ Failed to analyze database: {e}")


def vacuum_database(cursor: sqlite3.Cursor):
    """
    Run VACUUM to reclaim space and defragment.

    Args:
        cursor: Database cursor
    """
    try:
        cursor.execute("VACUUM")
        print("  ✓ Database vacuumed (space reclaimed)")
    except sqlite3.Error as e:
        print(f"  ✗ Failed to vacuum database: {e}")


def get_database_stats(cursor: sqlite3.Cursor) -> dict:
    """
    Get database statistics.

    Args:
        cursor: Database cursor

    Returns:
        dict: Database statistics
    """
    stats = {}

    # Count jobs
    cursor.execute("SELECT COUNT(*) FROM job")
    stats['total_jobs'] = cursor.fetchone()[0]

    # Count by status
    cursor.execute("SELECT status, COUNT(*) FROM job GROUP BY status")
    stats['by_status'] = dict(cursor.fetchall())

    # Database file size
    cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
    stats['db_size_bytes'] = cursor.fetchone()[0]
    stats['db_size_mb'] = stats['db_size_bytes'] / (1024 * 1024)

    # Count indexes
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
    stats['index_count'] = cursor.fetchone()[0]

    return stats


def print_stats(stats: dict, label: str):
    """Print database statistics."""
    print(f"\n{label}:")
    print(f"  Total jobs: {stats['total_jobs']:,}")
    print(f"  Database size: {stats['db_size_mb']:.2f} MB")
    print(f"  Indexes: {stats['index_count']}")
    print(f"  Jobs by status:")
    for status, count in stats.get('by_status', {}).items():
        print(f"    {status}: {count:,}")


# ============================================================================
# Main Migration
# ============================================================================

def run_migration(db_path: str, skip_fts: bool = False, skip_vacuum: bool = False):
    """
    Run the complete database migration.

    Args:
        db_path: Path to SQLite database
        skip_fts: Skip full-text search setup
        skip_vacuum: Skip database vacuum
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"❌ Database not found: {db_path}")
        print(f"   Please check the path or run ARM to create the database first.")
        sys.exit(1)

    print(f"🔧 ARM Database Index Migration")
    print(f"=" * 60)
    print(f"Database: {db_path}")

    # Create backup
    backup_path = db_file.with_suffix('.db.backup')
    if not backup_path.exists():
        import shutil
        shutil.copy2(db_file, backup_path)
        print(f"✓ Backup created: {backup_path}")
    else:
        print(f"⏭  Backup already exists: {backup_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get initial stats
        print(f"\n📊 Database Statistics (Before):")
        initial_stats = get_database_stats(cursor)
        print_stats(initial_stats, "Current State")

        # Create indexes
        print(f"\n📑 Creating Indexes:")
        created_count = 0
        for index_def in INDEXES:
            if create_index(cursor, index_def):
                created_count += 1

        # Setup full-text search
        if not skip_fts:
            print(f"\n🔍 Setting up Full-Text Search:")
            if setup_full_text_search(cursor):
                created_count += 1

        # Analyze database
        print(f"\n🔬 Optimizing Query Planner:")
        analyze_database(cursor)

        # Commit changes
        conn.commit()
        print(f"\n✓ Changes committed to database")

        # Get final stats
        print(f"\n📊 Database Statistics (After):")
        final_stats = get_database_stats(cursor)
        print_stats(final_stats, "New State")

        # Vacuum if requested
        if not skip_vacuum and created_count > 0:
            print(f"\n🧹 Vacuuming Database:")
            vacuum_database(cursor)
            conn.commit()

        # Summary
        print(f"\n" + "=" * 60)
        if created_count > 0:
            print(f"✅ Migration Complete!")
            print(f"   Created {created_count} new indexes/tables")
            print(f"   Performance should be significantly improved")
        else:
            print(f"✅ Migration Complete!")
            print(f"   All indexes already exist - database is up to date")

        print(f"\n💡 Tips:")
        print(f"   - Test the API to verify improved performance")
        print(f"   - Monitor query times for /api/jobs endpoint")
        print(f"   - Use the FTS table for fast text search:")
        print(f"     SELECT * FROM job WHERE job_id IN")
        print(f"       (SELECT job_id FROM job_fts WHERE job_fts MATCH 'search term')")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"   Database rolled back - no changes made")
        sys.exit(1)

    finally:
        conn.close()


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add performance indexes to ARM database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use database from arm.yaml config
  python scripts/add_database_indexes.py

  # Specify database path
  python scripts/add_database_indexes.py --db-path /path/to/arm.db

  # Skip full-text search setup
  python scripts/add_database_indexes.py --skip-fts

  # Skip vacuum (faster but won't reclaim space)
  python scripts/add_database_indexes.py --skip-vacuum
        """
    )

    parser.add_argument(
        '--db-path',
        type=str,
        default=default_db,
        help=f'Path to SQLite database (default: {default_db})'
    )

    parser.add_argument(
        '--skip-fts',
        action='store_true',
        help='Skip full-text search setup'
    )

    parser.add_argument(
        '--skip-vacuum',
        action='store_true',
        help='Skip database vacuum (faster migration)'
    )

    args = parser.parse_args()

    run_migration(args.db_path, args.skip_fts, args.skip_vacuum)


if __name__ == "__main__":
    main()
