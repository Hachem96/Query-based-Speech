"""
Read-only catalog endpoints for the web frontend: videos, books, and the
available filter options. All file-path columns are returned as ``/media`` URLs.
"""
import random

from fastapi import APIRouter, HTTPException, Query, Request
from backend.api.db import query_all, to_media_url
from backend.api.limiter import limiter

router = APIRouter()

_VIDEO_COLUMNS = [
    "id", "name", "subject", "year", "caption",
    "linkToCover", "linkToMP4", "linkToPdf", "linkToSummaryPdf", "linkToTranslation",
]
_BOOK_COLUMNS = ["id", "Title", "Author", "Year", "caption", "linkToPdf", "linkToCover"]


def _shape_video(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "subject": row["subject"],
        "year": row["year"],
        "caption": row["caption"],
        "coverUrl": to_media_url(row["linkToCover"]),
        "videoUrl": to_media_url(row["linkToMP4"]),
        "transcriptionUrl": to_media_url(row["linkToPdf"]),
        "summaryUrl": to_media_url(row["linkToSummaryPdf"]),
        "translationUrl": to_media_url(row["linkToTranslation"]),
    }


def _shape_book(row):
    return {
        "id": row["id"],
        "title": row["Title"],
        "author": row["Author"],
        "year": row["Year"],
        "caption": row["caption"],
        "pdfUrl": to_media_url(row["linkToPdf"]),
        "coverUrl": to_media_url(row["linkToCover"]),
    }


@router.get("/videos")
@limiter.limit("60/minute")
def list_videos(request: Request, subject: str | None = None, year: int | None = None):
    cols = ", ".join(f'"{c}"' for c in _VIDEO_COLUMNS)
    sql = f'SELECT {cols} FROM "Video" WHERE 1=1'
    params = []
    if subject:
        sql += ' AND subject = %s'
        params.append(subject)
    if year is not None:
        sql += ' AND year = %s'
        params.append(year)
    sql += ' ORDER BY year DESC NULLS LAST, name'
    return [_shape_video(r) for r in query_all(sql, params)]


# Placeholder: returns 4-5 random videos regardless of ``q`` until real
# search is implemented. Must stay above ``/videos/{video_id}``.
@router.get("/videos/search")
@limiter.limit("30/minute")
def search_videos(request: Request, q: str = Query(..., min_length=1, max_length=200)):
    cols = ", ".join(f'"{c}"' for c in _VIDEO_COLUMNS)
    limit = random.randint(4, 5)
    rows = query_all(f'SELECT {cols} FROM "Video" ORDER BY random() LIMIT %s', [limit])
    return [_shape_video(r) for r in rows]


@router.get("/videos/{video_id}")
@limiter.limit("60/minute")
def get_video(request: Request, video_id: int):
    cols = ", ".join(f'"{c}"' for c in _VIDEO_COLUMNS)
    rows = query_all(f'SELECT {cols} FROM "Video" WHERE id = %s', [video_id])
    if not rows:
        raise HTTPException(status_code=404, detail="Video not found")
    return _shape_video(rows[0])


@router.get("/books")
@limiter.limit("60/minute")
def list_books(request: Request):
    cols = ", ".join(f'"{c}"' for c in _BOOK_COLUMNS)
    return [_shape_book(r) for r in query_all(f'SELECT {cols} FROM "Book" ORDER BY "Title"')]


@router.get("/books/{book_id}")
@limiter.limit("60/minute")
def get_book(request: Request, book_id: int):
    cols = ", ".join(f'"{c}"' for c in _BOOK_COLUMNS)
    rows = query_all(f'SELECT {cols} FROM "Book" WHERE id = %s', [book_id])
    if not rows:
        raise HTTPException(status_code=404, detail="Book not found")
    return _shape_book(rows[0])


@router.get("/filters")
@limiter.limit("60/minute")
def filter_options(request: Request):
    subjects = query_all(
        'SELECT DISTINCT subject FROM "Video" WHERE subject IS NOT NULL AND subject <> \'\' ORDER BY subject'
    )
    years = query_all(
        'SELECT DISTINCT year FROM "Video" WHERE year IS NOT NULL ORDER BY year DESC'
    )
    return {
        "subjects": [r["subject"] for r in subjects],
        "years": [r["year"] for r in years],
    }
