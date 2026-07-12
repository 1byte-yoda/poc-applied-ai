"""Database connection, async engine, session factory, and retry logic."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

logger = logging.getLogger(__name__)

# Async engine with connection pool (10 min, 20 max)
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=10,  # total max = pool_size + max_overflow = 20
    pool_pre_ping=True,
    echo=False,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Max retry attempts and base delay for exponential backoff
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session with retry logic.

    Retries up to 3 times with exponential backoff on connection failures.
    """
    last_exception: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with AsyncSessionLocal() as session:
                yield session
                return
        except OSError as exc:
            last_exception = exc
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "Database connection attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Database connection failed after %d attempts: %s",
                    MAX_RETRIES,
                    exc,
                )

    if last_exception:
        raise last_exception


async def init_db() -> None:
    """Initialize the database: verify connectivity and create tables if missing."""
    from app.models.course import Base  # noqa: F401 — imports register all models

    # Import all models so Base.metadata knows about them
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        # Create all tables that don't already exist (idempotent)
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized — tables verified/created.")


async def close_db() -> None:
    """Dispose of the engine and close all connections."""
    await engine.dispose()
    logger.info("Database connections closed.")
