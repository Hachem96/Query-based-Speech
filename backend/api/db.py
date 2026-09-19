"""
Shared helpers for the REST API: a plain psycopg2 connection (same env-var
contract as the rest of ``backend/*``) and DB-path -> ``/media`` URL conversion.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Root directory the API serves media files from. ``Video``/``Book`` path
# columns are stored relative to it (see frontend/app.py:convert_to_media_url).
MAIN_MEDIA_PATH = os.getenv("MAIN_MEDIA_PATH", "")

# When set (e.g. an R2 public/custom domain), media URLs point there instead
# of the local ``/media`` proxy, so video/PDF bytes never touch this box.
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "").rstrip("/")

_NOT_AVAILABLE = {None, "", "Not Available", "nan", "None"}


def get_connection():
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
    )
    connection.autocommit = True
    return connection


def query_all(sql, params=None):
    """Run a SELECT and return a list of dict rows."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def to_media_url(db_path):
    """Convert a stored file path to a web-servable ``/media/...`` URL."""
    if db_path is None:
        return None
    db_path = str(db_path).strip()
    if db_path in _NOT_AVAILABLE:
        return None

    if MAIN_MEDIA_PATH and db_path.startswith(MAIN_MEDIA_PATH):
        rel = db_path[len(MAIN_MEDIA_PATH):]
    else:
        rel = db_path
    rel = rel.lstrip("/\\").replace("\\", "/")
    if MEDIA_BASE_URL:
        return f"{MEDIA_BASE_URL}/{rel}"
    return f"/media/{rel}"
