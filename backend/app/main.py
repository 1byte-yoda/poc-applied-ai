"""FastAPI application entry point for the learning platform."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB on startup, close on shutdown."""
    try:
        await init_db()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    # Seed courses on first run if database is empty
    try:
        await _seed_if_empty()
    except Exception as e:
        logger.warning("Database seeding skipped or failed: %s", e)

    yield
    await close_db()


async def _seed_if_empty() -> None:
    """Seed courses from tree files if the database is empty."""
    from pathlib import Path

    from sqlalchemy import func, select

    from app.db import AsyncSessionLocal
    from app.models import Course
    from app.services.tree_parser import parse_tree_file, seed_database

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Course.id)))
        count = result.scalar_one()
        if count > 0:
            logger.info("Database already contains %d courses, skipping seed.", count)
            return

    # Look for tree files in data/ directory
    data_dir = Path("data")
    tree_files = [
        ("Applied AI Diploma", "applied_diploma_ai_ml.txt", "applied_diploma_ai_ml/"),
        ("Applied Roots", "applied_roots.txt", "applied_roots/"),
    ]

    for course_name, filename, path_prefix in tree_files:
        file_path = data_dir / filename
        if not file_path.exists():
            # Also check project root
            file_path = Path(filename)
        if not file_path.exists():
            logger.warning("Tree file not found: %s", filename)
            continue

        logger.info("Seeding course %r from %s", course_name, file_path)
        root_node = parse_tree_file(str(file_path))
        await seed_database(course_name, root_node, source_file=filename, path_prefix=path_prefix)


app = FastAPI(
    title="Learning Platform API",
    description="API for browsing courses and consuming multi-format content.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OSError)
async def database_error_handler(request: Request, exc: OSError):
    """Handle database connection errors with 503 + Retry-After."""
    logger.error("Database connection error: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable. Please retry later."},
        headers={"Retry-After": "5"},
    )


# Include routers
from app.routers.courses import router as courses_router  # noqa: E402
from app.routers.lectures import router as lectures_router  # noqa: E402

app.include_router(courses_router, prefix="/api")
app.include_router(lectures_router, prefix="/api")
