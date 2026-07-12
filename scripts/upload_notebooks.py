"""CLI script to upload .ipynb files to Google Drive and update colab_mappings table.

Usage:
    uv run python scripts/upload_notebooks.py --directory ./media/notebooks
    uv run python scripts/upload_notebooks.py --file ./media/notebooks/example.ipynb
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db import close_db, init_db
from app.services.colab_integration import ColabIntegrationService


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload .ipynb notebooks to Google Drive and store Colab URL mappings."
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Directory containing .ipynb files to batch upload.",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Single .ipynb file to upload.",
    )
    args = parser.parse_args()

    if not args.directory and not args.file:
        parser.error("Either --directory or --file must be specified.")

    await init_db()
    service = ColabIntegrationService()

    try:
        if args.directory:
            mappings = await service.batch_upload(args.directory)
            print(f"Successfully uploaded {len(mappings)} notebook(s).")
            for m in mappings:
                print(f"  {m.filename} -> {m.colab_url}")
        elif args.file:
            mapping = await service.upload_and_map(args.file)
            if mapping:
                print(f"Uploaded: {mapping.filename} -> {mapping.colab_url}")
            else:
                print("File was already mapped or could not be uploaded.")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
