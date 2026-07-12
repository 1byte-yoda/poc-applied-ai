"""Content resolution service for serving lecture content by type."""

import html
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ColabMapping, Lecture
from app.utils.path_security import validate_media_path

# MIME type mapping for streaming content
_MIME_TYPES = {
    "mp4": "video/mp4",
    "pdf": "application/pdf",
    "mp3": "audio/mpeg",
    "png": "image/png",
    "zip": "application/zip",
}

# HTML template for wrapping text/html content
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }}
        pre {{
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
{content}
</body>
</html>"""


async def resolve_lecture_content(
    lecture_id: int,
    session: AsyncSession,
) -> FileResponse | RedirectResponse | HTMLResponse:
    """Resolve and serve lecture content based on its content type.

    Args:
        lecture_id: The database ID of the lecture.
        session: Active async database session.

    Returns:
        FileResponse for streamable media (mp4, pdf, mp3).
        RedirectResponse (307) for ipynb → Colab.
        HTMLResponse for docx and txt content.

    Raises:
        HTTPException(404): Lecture not found, file not found, or Colab URL missing.
        HTTPException(415): Unsupported content type.
    """
    result = await session.execute(
        select(Lecture).where(Lecture.id == lecture_id)
    )
    lecture = result.scalar_one_or_none()

    if lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    content_type = lecture.content_type

    # Streamable binary content (mp4, pdf, mp3, png, zip)
    if content_type in _MIME_TYPES:
        if not lecture.file_path:
            raise HTTPException(status_code=404, detail="Media file path not configured")

        full_path = validate_media_path(lecture.file_path, settings.MEDIA_ROOT)

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")

        # For PDFs and images, serve inline (viewable in browser)
        # For other types, use attachment (triggers download)
        content_disposition = "inline" if content_type in ("pdf", "png") else None

        return FileResponse(
            path=str(full_path),
            media_type=_MIME_TYPES[content_type],
            filename=lecture.original_filename or lecture.title,
            content_disposition_type="inline" if content_type in ("pdf", "png") else "attachment",
        )

    # Notebook → redirect to Colab
    if content_type == "ipynb":
        mapping_result = await session.execute(
            select(ColabMapping).where(
                ColabMapping.filename == lecture.original_filename
            )
        )
        mapping = mapping_result.scalar_one_or_none()

        if mapping is None or mapping.colab_url is None:
            raise HTTPException(
                status_code=404,
                detail="Colab URL not configured for this notebook",
            )

        return RedirectResponse(url=mapping.colab_url, status_code=307)

    # DOCX → convert to HTML
    if content_type == "docx":
        if not lecture.file_path:
            raise HTTPException(status_code=404, detail="File path not configured")

        full_path = validate_media_path(lecture.file_path, settings.MEDIA_ROOT)

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        from app.utils.docx_renderer import convert_docx_to_html

        html_content = convert_docx_to_html(full_path)
        rendered = _HTML_TEMPLATE.format(title=lecture.title, content=html_content)
        return HTMLResponse(content=rendered)

    # TXT → wrap in preformatted HTML
    if content_type == "txt":
        if not lecture.file_path:
            raise HTTPException(status_code=404, detail="File path not configured")

        full_path = validate_media_path(lecture.file_path, settings.MEDIA_ROOT)

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        text_content = full_path.read_text(encoding="utf-8")
        escaped = html.escape(text_content)
        pre_content = f"<pre>{escaped}</pre>"
        rendered = _HTML_TEMPLATE.format(title=lecture.title, content=pre_content)
        return HTMLResponse(content=rendered)

    # HTML → serve directly in template
    if content_type == "html":
        if not lecture.file_path:
            raise HTTPException(status_code=404, detail="File path not configured")

        full_path = validate_media_path(lecture.file_path, settings.MEDIA_ROOT)

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        html_content = full_path.read_text(encoding="utf-8")
        rendered = _HTML_TEMPLATE.format(title=lecture.title, content=html_content)
        return HTMLResponse(content=rendered)

    # Unsupported content type
    raise HTTPException(
        status_code=415,
        detail=f"Unsupported content type: {content_type}",
    )
