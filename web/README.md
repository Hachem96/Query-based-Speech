# Es2al Sayed — Next.js frontend

RTL Arabic web UI for the Query-based Speech Retrieval system. Talks to the
FastAPI backend (`backend/api/main.py`) over HTTP — it does **not** import the
Python retrieval code the way the Dash app (`frontend/app.py`) does.

## Prerequisites

The backend must be running and reachable:

```bash
# from the repo root
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

The backend needs (as always) `DB_*` env vars, `MAIN_MEDIA_PATH`, and the
`Qwen_API_KEY` / `API_KEY_QWENEMBEDDING` placeholders. New env var:

- `FRONTEND_ORIGINS` — comma-separated allowed CORS origins
  (default `http://localhost:3000`).

## Run

```bash
cd web
cp .env.example .env.local     # adjust NEXT_PUBLIC_API_BASE if the backend isn't on :8000
pnpm install
pnpm dev                       # http://localhost:3000
```

Uses **pnpm** (pinned via `packageManager` in `package.json`; `corepack enable`
picks it up automatically). `pnpm build` / `pnpm start` for production.

## What it uses from the backend

| UI                          | Endpoint                        |
| --------------------------- | ------------------------------- |
| Video list + filters        | `GET /api/videos`, `GET /api/filters` |
| Video page                  | `GET /api/videos/{id}`          |
| Books list / viewer         | `GET /api/books`, `GET /api/books/{id}` |
| Q&A → seek                  | `POST /inference/`              |
| mp4 / covers / PDFs         | `GET /media/{path}`             |

`/media` uses `FileResponse`, which answers HTTP `Range` requests — required for
`<video>` seeking (and for playback to start at all in Safari/iOS).

## Structure

```
app/
  layout.tsx            RTL shell (<html lang="ar" dir="rtl">) + nav
  page.tsx              video grid; subject/year filters live in the URL (?subject=&year=)
  videos/[id]/page.tsx  server-fetches the video, renders <VideoWatch>
  books/page.tsx
  books/[id]/page.tsx   PDF in an <iframe>
components/
  Filters.tsx           client; pushes filter changes to the URL
  VideoCard.tsx
  VideoWatch.tsx        client; <video> ref, calls /inference, seeks to the result.
                        Deep link: /videos/1?t=125 starts at 125s.
lib/api.ts              typed fetch wrappers; mediaUrl() prefixes /media paths with API base
```

## Deploy

Frontend on any Node host (Vercel or self-hosted `pnpm start`). The backend must
be able to see Postgres **and** the `MAIN_MEDIA_PATH` disk. Put both behind one
domain with a reverse proxy: `/api`, `/media`, `/inference` → FastAPI, everything
else → Next. Set `NEXT_PUBLIC_API_BASE` to the public backend URL and add the
frontend's origin to `FRONTEND_ORIGINS`.
