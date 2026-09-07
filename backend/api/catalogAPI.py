"""
Read-only catalog endpoints for the web frontend: videos, books, and the
available filter options. All file-path columns are returned as ``/media`` URLs.
"""
from fastapi import APIRouter, HTTPException
from backend.api.db import query_all, to_media_url

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
def list_videos(subject: str | None = None, year: int | None = None):
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


@router.get("/videos/{video_id}")
def get_video(video_id: int):
    cols = ", ".join(f'"{c}"' for c in _VIDEO_COLUMNS)
    rows = query_all(f'SELECT {cols} FROM "Video" WHERE id = %s', [video_id])
    if not rows:
        raise HTTPException(status_code=404, detail="Video not found")
    return _shape_video(rows[0])


@router.get("/books")
def list_books():
    cols = ", ".join(f'"{c}"' for c in _BOOK_COLUMNS)
    return [_shape_book(r) for r in query_all(f'SELECT {cols} FROM "Book" ORDER BY "Title"')]


@router.get("/books/{book_id}")
def get_book(book_id: int):
    cols = ", ".join(f'"{c}"' for c in _BOOK_COLUMNS)
    rows = query_all(f'SELECT {cols} FROM "Book" WHERE id = %s', [book_id])
    if not rows:
        raise HTTPException(status_code=404, detail="Book not found")
    return _shape_book(rows[0])


@router.get("/filters")
def filter_options():
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
