"""Colab integration service for uploading notebooks and managing URL mappings."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import ColabMapping

logger = logging.getLogger(__name__)

# Colab URL format
_COLAB_URL_TEMPLATE = "https://colab.research.google.com/drive/{file_id}"


class ColabIntegrationService:
    """Service for managing Google Colab notebook mappings.

    Handles uploading .ipynb files to Google Drive and maintaining
    a mapping table between local filenames and Colab URLs.
    """

    async def get_colab_url(self, filename: str) -> str | None:
        """Look up the Colab URL for a given notebook filename.

        Args:
            filename: The notebook filename to look up.

        Returns:
            The Colab URL string, or None if no mapping exists.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ColabMapping).where(ColabMapping.filename == filename)
            )
            mapping = result.scalar_one_or_none()
            if mapping is None:
                return None
            return mapping.colab_url

    async def upload_and_map(self, local_path: str) -> ColabMapping | None:
        """Upload a notebook to Google Drive and store the mapping.

        Args:
            local_path: Local filesystem path to the .ipynb file.

        Returns:
            The created ColabMapping record, or None if upload failed.

        Raises:
            FileNotFoundError: If the local file does not exist.
        """
        path = Path(local_path)
        if not path.exists():
            raise FileNotFoundError(f"Notebook file not found: {local_path}")

        if not path.suffix.lower() == ".ipynb":
            logger.warning("File %s is not a .ipynb file, skipping.", local_path)
            return None

        filename = path.name

        # Check if already mapped
        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(ColabMapping).where(ColabMapping.filename == filename)
            )
            if existing.scalar_one_or_none() is not None:
                logger.info("File %s already mapped, skipping.", filename)
                return None

        # Upload to Google Drive
        try:
            file_id = await self._upload_to_drive(local_path)
        except Exception as e:
            logger.error("Failed to upload %s to Google Drive: %s", filename, e)
            return None

        colab_url = _COLAB_URL_TEMPLATE.format(file_id=file_id)

        # Store mapping in database
        async with AsyncSessionLocal() as session:
            async with session.begin():
                mapping = ColabMapping(
                    filename=filename,
                    local_path=str(path.resolve()),
                    google_drive_file_id=file_id,
                    colab_url=colab_url,
                    uploaded_at=datetime.now(timezone.utc),
                )
                session.add(mapping)

        logger.info("Uploaded and mapped: %s -> %s", filename, colab_url)
        return mapping

    async def batch_upload(self, directory: str) -> list[ColabMapping]:
        """Upload all .ipynb files in a directory and store their mappings.

        Files that are already mapped are skipped. Errors on individual files
        are logged and do not halt processing of remaining files.

        Args:
            directory: Path to directory containing .ipynb files.

        Returns:
            List of successfully created ColabMapping records.
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        ipynb_files = sorted(dir_path.glob("**/*.ipynb"))
        results: list[ColabMapping] = []

        for file_path in ipynb_files:
            try:
                mapping = await self.upload_and_map(str(file_path))
                if mapping is not None:
                    results.append(mapping)
            except Exception as e:
                logger.error(
                    "Error processing %s: %s. Continuing with remaining files.",
                    file_path.name,
                    e,
                )
                continue

        logger.info(
            "Batch upload complete: %d/%d files uploaded.",
            len(results),
            len(ipynb_files),
        )
        return results

    async def _upload_to_drive(self, local_path: str) -> str:
        """Upload a file to Google Drive and return the file ID.

        This method uses the Google Drive API via google-api-python-client.
        Requires valid Google credentials configured in the environment.

        Args:
            local_path: Path to the file to upload.

        Returns:
            The Google Drive file ID string.

        Raises:
            Exception: If the upload fails.
        """
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.service_account import Credentials

        # Load credentials from service account file
        # The credentials path should be configured via environment variable
        import os

        creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not creds_path:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_FILE environment variable not set. "
                "Cannot upload to Google Drive."
            )

        credentials = Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )

        service = build("drive", "v3", credentials=credentials)

        file_metadata = {"name": Path(local_path).name}
        media = MediaFileUpload(
            local_path,
            mimetype="application/x-ipynb+json",
            resumable=True,
        )

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        return file["id"]
