"""
Serve media files (mp4, cover images, PDFs) from ``MAIN_MEDIA_PATH``.

Starlette's ``FileResponse`` emits ``Accept-Ranges`` and answers ``Range``
requests with ``206 Partial Content``, which the browser ``<video>`` element
needs for seeking (and Safari/iOS need just to start playback).
"""
import mimetypes
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.api.db import MAIN_MEDIA_PATH

router = APIRouter()

_ROOT = os.path.abspath(MAIN_MEDIA_PATH) if MAIN_MEDIA_PATH else ""


@router.get("/{path:path}")
def get_media(path: str):
    if not _ROOT:
        raise HTTPException(status_code=500, detail="MAIN_MEDIA_PATH is not configured")

    full_path = os.path.abspath(os.path.join(_ROOT, path))
    # Prevent path traversal outside the media root.
    if os.path.commonpath([_ROOT, full_path]) != _ROOT:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
    return FileResponse(full_path, media_type=media_type)
