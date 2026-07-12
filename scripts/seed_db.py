"""Seed the database with course data from tree text files.

Usage:
    cd backend && uv run python ../scripts/seed_db.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db import close_db, init_db
from app.services.tree_parser import parse_tree_file, seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tree files to seed
TREE_FILES = [
    ("Applied AI Diploma", "applied_diploma_ai_ml.txt"),
    ("Applied Roots", "applied_roots.txt"),
]


async def main() -> None:
    """Initialize DB and seed courses from tree files."""
    await init_db()

    try:
        data_dir = Path("data")
        project_root = Path(__file__).resolve().parent.parent

        for course_name, filename in TREE_FILES:
            # Check data/ directory first, then project root
            file_path = data_dir / filename
            if not file_path.exists():
                file_path = project_root / filename
            if not file_path.exists():
                logger.warning("Tree file not found: %s, skipping.", filename)
                continue

            logger.info("Parsing tree file: %s", file_path)
            root_node = parse_tree_file(str(file_path))

            logger.info("Seeding course: %s", course_name)
            await seed_database(course_name, root_node, source_file=filename)

        logger.info("Seeding complete.")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
