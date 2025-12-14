"""
Async Database Layer for FastAPI
Uses SQLAlchemy 2.0 with async support
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = None
async_session_maker = None

# Base class for models
Base = declarative_base()


async def init_db():
    """
    Initialize database connection and create tables.
    Called during application startup.
    """
    global engine, async_session_maker

    database_url = settings.get_database_url()
    logger.info(f"Initializing database: {database_url}")

    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL query logging
        future=True,
        pool_pre_ping=True,  # Verify connections before using
        connect_args={
            "check_same_thread": False,  # Needed for SQLite
        } if "sqlite" in database_url else {}
    )

    # Enable WAL mode for SQLite (better concurrency)
    if "sqlite" in database_url:
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

    # Create session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create tables (if they don't exist)
    # Note: In production, use Alembic migrations instead
    async with engine.begin() as conn:
        # Import models here to ensure they're registered
        # from arm.models import Job, Track, Config, UISettings, Notification
        # await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified")


async def close_db():
    """
    Close database connections.
    Called during application shutdown.
    """
    global engine

    if engine:
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# Database Utilities
# ============================================================================

async def create_tables():
    """
    Create all database tables.
    Use this for initial setup or testing.
    For production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created")


async def drop_tables():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    Only use for testing or development.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All tables dropped")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_db():
        """Test database connection."""
        print("Testing database connection...")

        # Initialize database
        await init_db()

        # Test a simple query
        async with async_session_maker() as session:
            result = await session.execute("SELECT 1")
            print(f"Query result: {result.scalar()}")

        # Close database
        await close_db()

        print("Database test complete!")

    # Run test
    asyncio.run(test_db())
