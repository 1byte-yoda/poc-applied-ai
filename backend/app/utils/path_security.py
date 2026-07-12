"""Path security utilities to prevent directory traversal attacks."""

from pathlib import Path

from fastapi import HTTPException


def validate_media_path(file_path: str, media_root: str) -> Path:
    """Validate that a file path resolves within the configured media root.

    Prevents directory traversal attacks by ensuring the resolved absolute
    path is a descendant of the media root directory.

    Args:
        file_path: The relative file path to validate (from database).
        media_root: The absolute path to the media volume root.

    Returns:
        The resolved absolute Path if validation passes.

    Raises:
        HTTPException(403): If the path would escape the media root.
        HTTPException(404): If the resolved file does not exist.
    """
    root = Path(media_root).resolve()

    # Reject obviously malicious patterns before resolution
    if file_path.startswith("/") or ".." in file_path.split("/"):
        raise HTTPException(
            status_code=403,
            detail="Access denied: invalid file path",
        )

    # Resolve the full path
    full_path = (root / file_path).resolve()

    # Verify the resolved path is within the media root
    try:
        full_path.relative_to(root)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied: invalid file path",
        )

    return full_path
