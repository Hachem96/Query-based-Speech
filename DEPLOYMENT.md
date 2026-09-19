# Deployment Plan — Es2al Sayed / إسأل سيد

Scope: deploy the **Next.js** frontend (`web/`) + **FastAPI** backend (`backend/`) publicly,
build and seed the PostgreSQL + pgvector database from the videos on the external drive,
and host all media (mp4 / covers / PDFs) on object storage.

Everything below is derived from reading the repo on 2026-09-07. Where a fact could not be
verified from the machine (the external drive is not mounted, the DB does not exist yet),
it is called out as **VERIFY** with the exact command to run — do not skip those.

---

## 0. TL;DR — recommended architecture

| Layer | Recommendation | Est. cost / month |
|---|---|---|
| Object storage (mp4, covers, PDFs) | **Cloudflare R2** + public bucket domain | ~$0.015/GB storage, **$0 egress**. 100 GB ≈ **$1.50** |
| Database (Postgres 16 + pgvector) | **Self-hosted on the same VPS** via `pgvector/pgvector:pg16` Docker image, with a nightly `pg_dump` to R2. Managed **Neon** is the fallback if you don't want to run backups. | **$0** self-hosted / **$0–19** Neon |
| Backend (FastAPI + local embedding model) | **One small VPS** (Hetzner CX22 = 2 vCPU / 4 GB ≈ €4.5, or CX32 / 8 GB ≈ €7 recommended — the SentenceTransformer model needs ~1.5 GB resident). Dockerised. | **€4.5–7** (~$5–8) |
| Frontend (Next.js 15 SSR) | Same VPS, `pnpm build && pnpm start`, behind **Caddy** (auto-HTTPS) reverse proxy. Vercel Hobby (free, non-commercial) is the alternative. | **$0** (shares the VPS) |
| DNS / TLS | Cloudflare DNS (free) + Caddy on the box | **$0** |

**Total: roughly $7–10/month** self-hosting DB + frontend on the one VPS, plus R2 storage
proportional to video size. Using Neon instead adds $0–19.

```
                      ┌───────────── one VPS (Hetzner) ─────────────┐
   browser  ──HTTPS──▶│  Caddy :443                                 │
                      │    ├── /  , /videos/* , /books/*  ─▶ Next :3000
                      │    └── /api/* , /inference/* , /media/*  ─▶ FastAPI :8000
                      │                                     │        │
                      │  Postgres+pgvector :5432 (Docker) ◀──┘        │
                      └─────────────────────────────────────────────┘
   <video src>  ──────────────────────────────────────────▶  Cloudflare R2 (public)
```

The FastAPI container serves inference + catalog JSON. Video bytes are served **directly
from R2** (see code change #4) so the VPS never needs the multi-hundred-GB media disk.

---

## 1. STOP — verify this before planning anything else

`processVideo/addNewVideo.py:2` has the ASR import commented out:

```python
#from ASR.SpeechTextConversion import transcribe_One_Speech
```

So `add_new_video(..., transcribe=True)` will crash, and only `transcribe=False` works —
which **requires a pre-existing transcription JSON per video** at
`<video folder>/Transcription/transcription_whisper_large_v3.json`
(`addNewVideo.py:59`).

**VERIFY (mount the TOSHIBA drive first):**

```bash
DRIVE="/Volumes/TOSHIBA EXT/Personal/PromptSpeech"
find "$DRIVE" -name "*.mp4" | wc -l
find "$DRIVE" -name "transcription_whisper_large_v3.json" | wc -l
find "$DRIVE" -name "caption.txt" | wc -l
du -sh "$DRIVE"
# expected layout per addNewVideo.py: <MainFolder>/<Year>/<VideoName>/<VideoName>.mp4
find "$DRIVE" -maxdepth 3 -type d | head -30
```

**Branch A — the two counts roughly match** (transcriptions already exist):
ingestion is a *fix-two-bugs-and-run* job (Section 4). Proceed with this plan.

**Branch B — the transcription count is ~0:**
this is **not a deployment task**, it is a transcription project first:
Whisper `large-v3` + `pyannote/speaker-diarization-3.1` (a **gated** Hugging Face model
requiring token + license acceptance) over the whole corpus, ideally on a rented GPU,
through `ASR/SpeechTextConversion.py` + the currently-disabled code path in `addNewVideo.py`
which **has never been run end to end** in this repo. Budget days, not hours. Decide this
explicitly before continuing.

Also record the numbers — they size the database (Section 6).

---

## 2. Required code changes (before any deploy)

All are small and localised. Do them on a branch, test locally (Section 3), then ship.

**Status as of 2026-09-19: 2.1, 2.2, 2.3, 2.4, 2.5 done. 2.6/2.7 need an env var set at
deploy time, not a code change. 2.8 not done (cosmetic). 2.9 partially done — see the note
at the end of 2.9, secrets are still in git history.** Also fixed this session, not in the
original plan: a DB-connection leak in `InferenceQuery.py` (every `/inference` call opened a
connection and never closed it — would have exhausted Postgres `max_connections` under any
sustained traffic, attack or not), a broken `torch==2.14.0` pin (no such version exists;
pinned to `2.4.1`, verified against `sentence-transformers==6.0.1`'s `torch>=2.2`
requirement), a symlink bypass of the media path-traversal guard (`abspath` → `realpath`),
and error-leakage in `/inference` (raw exception text returned to the client; unknown
`videoName` now returns 404 instead of a 500 with a pandas stack message). Rate limiting
(`slowapi`, see Section 2.10) was also added — it did not exist anywhere before this.

### 2.1 — `backend/api/main.py` is behind the rest of the code (CRITICAL) — DONE

Current file mounts **only** `/inference` and `/table`. It does **not** mount the catalog
or media routers and has **no CORS**, yet `web/lib/api.ts` calls `/api/videos`,
`/api/books`, `/api/filters`, `/media/*`, and the browser calls `/inference/` cross-origin.
The Next.js app cannot work against `main.py` as written.

Rewrite to:

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.inferenceAPI import router as inference_router
from backend.api.catalogAPI import router as catalog_router
from backend.api.mediaAPI import router as media_router   # keep only if NOT using R2 (see 2.4)

app = FastAPI()

origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(inference_router, prefix="/inference", tags=["Inference"])
app.include_router(catalog_router,   prefix="/api",       tags=["Catalog"])
app.include_router(media_router,     prefix="/media",     tags=["Media"])   # only if not using R2
```

### 2.2 — Do NOT mount `/table` publicly (security) — DONE

`backend/api/getTableInfoAPI.py` → `backend/searchinDatabase.py:get_table_from_db()` builds
`f'SELECT {columns_str} FROM "{Table_Name}"'` from the **request body**. Table and column
names are string-interpolated from user input = arbitrary read of any table/column.
Leave `table_info_router` unmounted (done above by omission). Delete the file if unused.

### 2.3 — Fix the `add_row("Video")` bug in `backend/DataBaseFunctions.py` — DONE

`add_row()` (~line 178) has:

```python
if(table_name=="Video"):
    videoName = columnValues["name"]
    exists = videoIsExist(configuration,videoName)   # `configuration` is undefined; wrong arity
```

`configuration` is never defined and the real signature is `videoIsExist(videoName)`.
The bare `except Exception` swallows the `NameError`, `add_row` returns `None`, so every
`InitialChunks` / `MergedChunks` / `Embeddings` row is inserted with `videoId = NULL`.

`add_new_video()` already does its own existence check (`addNewVideo.py:38`), so **delete
this whole `if table_name=="Video"` block**. (Same class of bug in
`processVideo/addNewBook.py:25` — `bookIsExist(title, author)` vs 3-param signature — fix
only if you ingest books.)

### 2.4 — Serve media from R2 instead of the `/media` proxy — CODE DONE, NOT YET ACTIVE

This is not a cost optimization, it's an availability fix: as long as media flows through
`mediaAPI.py`, video/cover/PDF bytes compete with the embedding model for CPU on the same
small VPS, and a handful of clients scrubbing a video can saturate the box. `to_media_url()`
now emits an R2 URL when `MEDIA_BASE_URL` is set, and `main.py` now mounts `mediaAPI` **only
when `MEDIA_BASE_URL` is unset** — so locally (no R2 yet) it still works exactly as before,
and once you set the env var in production the proxy route is not even registered.

```python
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "")  # e.g. https://media.es2alsayed.com

def to_media_url(db_path):
    if db_path is None:
        return None
    db_path = str(db_path).strip()
    if db_path in _NOT_AVAILABLE:
        return None
    rel = db_path
    if MAIN_MEDIA_PATH and rel.startswith(MAIN_MEDIA_PATH):
        rel = rel[len(MAIN_MEDIA_PATH):]
    rel = rel.lstrip("/\\").replace("\\", "/")
    if MEDIA_BASE_URL:
        return f"{MEDIA_BASE_URL}/{rel}"
    return f"/media/{rel}"      # local-dev fallback
```

`web/lib/api.ts:mediaUrl()` already passes through anything matching `^https?://` untouched,
so **the frontend needs no change**. With `MEDIA_BASE_URL` set you can drop `mediaAPI` from
`main.py` entirely and the backend never touches video files.

The DB stores paths as `{MainFolder}/{Year}/{VideoName}/{VideoName}.mp4`
(`addNewVideo.py:100-118`). Upload the tree to R2 preserving that structure (Section 5.2)
and the keys line up with zero DB rewriting.

### 2.5 — `backend/requirements.txt` is incomplete — DONE

Added `sentence-transformers==6.0.1` + `torch==2.4.1` (verified: 6.0.1 requires
`torch>=2.2`, so this pair actually resolves — an earlier pass at this pinned a
nonexistent `torch==2.14.0`, which would have hard-failed the Docker build; verify any
future pin bump against PyPI before trusting it) and `slowapi` (Section 2.10).

Keep `psycopg2` → `psycopg2-binary` for the container unless you install libpq/build tools.

### 2.6 — `Qwen_API_KEY` must be set even though it's unused

`backend/embedding.py:17` does `OpenAI(api_key=os.getenv("Qwen_API_KEY"), ...)` at import.
The openai v1 SDK raises if the key is `None`. The active path uses the **local** model, so
set `Qwen_API_KEY=unused` (any non-empty string) in the backend environment. Same for
`API_KEY_QWENEMBEDDING` if you run `processVideo/` code.

### 2.7 — `DB_USER` (verify against your provider)

`user="postgres"` is hard-coded in **five** places: `backend/api/db.py:19`,
`backend/InferenceQuery.py:17`, `backend/searchinDatabase.py:8`, and twice in
`backend/DataBaseFunctions.py`. Self-hosted Postgres uses `postgres`, so if you self-host
(recommended) **no change needed**. If you use Neon/Supabase and the role is not `postgres`,
thread a `DB_USER` env var through all five `psycopg2.connect(...)` calls.

Note `DataBaseFunctions.create_database()` runs `CREATE DATABASE` while connected to
`dbname="postgres"` — fine for self-hosted, **not possible on Neon** (DB is pre-provisioned).
In that case run only `creat_db_tables()` and do `CREATE EXTENSION vector;` by hand first.

### 2.8 — `common.py` hard-coded font path (only if covers matter)

`processVideo/common.py:7`: `font_path = "/mnt/d/Personal/PromptSpeech/Amiri/Amiri-Bold.ttf"`.
Missing → `ImageFont.load_default()`, which **cannot render Arabic**. Make it an env var and
ship an Amiri `.ttf`, or accept blank/garbled cover images. (The catalog also works with
`coverUrl: null`.)

### 2.9 — Rotate committed secrets before going public — WORKING TREE SCRUBBED, CREDENTIALS STILL LIVE

Both were removed from the current files (the DeepSeek key comment deleted;
`ExportVideoApp.py` now reads `TELEGRAM_API_ID`/`TELEGRAM_API_HASH`/`TELEGRAM_PHONE` from
env vars). **This does not make the credentials safe** — both are still fetchable from git
history (`git log -p -S '7b01d9b55b6b7adcf14446a017e46d20'` finds the commit). The only
actions that actually matter:

- Revoke the DeepSeek key at the provider and issue a new one.
- Reset the Telegram app credentials at my.telegram.org (the phone number itself can't be
  "rotated" — treat it as exposed).
- Decide on `git filter-repo` (rewrites history, breaks any existing clones/forks) if this
  repo is going public. If it stays private, revoking the credentials is probably enough.
- (Checked this session: no Telethon `.session` file was ever committed — that would have
  been a live authenticated login, worse than the api_hash.)

---

### 2.10 — Rate limiting & abuse surface — DONE (app-level), CADDY WIRING STILL NEEDED

Nothing rate-limited anything before this session. Given the feature set — public,
unauthenticated, one CPU-expensive endpoint — this is the actual security story for this
app, more than SQL injection or auth (there's no auth surface; the DB access patterns were
already parameterized correctly except the now-removed `/table` route).

Added `slowapi` (`backend/api/limiter.py`, shared `Limiter` instance):
- `POST /inference/` — **10/minute per key** (the expensive one: an embedding model forward
  pass + a full per-video vector scan on every call).
- `/api/*` (catalog) — 60/minute per key.
- `/media/*` — 120/minute per key (only mounted when `MEDIA_BASE_URL` is unset — see 2.4).
- `InferenceRequest.query`/`videoName` now have `max_length` (500 / 200) to stop
  oversized-payload abuse of the embedding model.
- `/inference/`'s exception handler no longer leaks `str(e)` to the client (logs
  server-side instead), and an unknown `videoName` returns 404 instead of a 500 with a
  pandas stack trace.

**Not yet done — required before this is actually effective in production:**

- `slowapi`'s default key function (`get_remote_address`) reads the TCP peer address. Behind
  Caddy that's `127.0.0.1` for *every* request — so today's config either rate-limits all
  users as one shared bucket or does nothing. Fix: Caddy must forward the real client IP
  (`header_up X-Forwarded-For {remote_host}` — Caddy does this by default via
  `reverse_proxy`, verify it's not stripped), and uvicorn must trust it:
  `uvicorn backend.api.main:app --proxy-headers --forwarded-allow-ips='127.0.0.1'` (tighten
  the IP to Caddy's actual address). Without this, treat rate limiting as **not deployed**
  even though the code is there.
- Put Cloudflare in front (orange-cloud DNS) for `es2alsayed.com` (the HTML/API origin
  only — not the R2 media domain) for free WAF/bot-fight rules as a second layer above the
  app-level limits.
- **"Watch, not download" is not enforceable** for a plain `<video src>` served over HTTP —
  anything the browser can play, the user can save (view-source, devtools network tab, or a
  downloader extension). The realistic options are friction, not prevention: short-lived
  signed R2 URLs (re-signed per page load) or HLS segmentation. Don't represent the current
  design as preventing downloads in any user-facing copy.
- No CSP/security headers existed on the Next.js side; added in `web/next.config.mjs`
  (`X-Frame-Options`, `X-Content-Type-Options`, a CSP scoped to `NEXT_PUBLIC_API_BASE` +
  Google Fonts, `Permissions-Policy` disabling camera/mic/geolocation). Re-check the CSP if
  you add any third-party script/embed later — it's currently locked to `'self'`.

---

## 3. Phase 1 — local setup & test (do this first, on this Mac)

Prereqs on this machine: Docker ✓, pnpm ✓, node ✓, **ffmpeg ✗ (install: `brew install ffmpeg`)**,
Python is 3.14 — **too new**, `torch` / `sentence-transformers` have no 3.14 wheels yet.
Install 3.11: `brew install python@3.11`.

### 3.1 — Local Postgres + pgvector

```bash
docker run -d --name espg -p 5432:5432 \
  -e POSTGRES_PASSWORD=root -e POSTGRES_DB=SpeechDatabaseInfo \
  pgvector/pgvector:pg16
docker exec -it espg psql -U postgres -d SpeechDatabaseInfo -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3.2 — Backend venv + env

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt      # after edit 2.5

export DB_NAME=SpeechDatabaseInfo DB_PASSWORD=root DB_HOST=localhost DB_PORT=5432
export MAIN_MEDIA_PATH="/Volumes/TOSHIBA EXT/Personal/PromptSpeech"   # local: keep /media proxy
export Qwen_API_KEY=unused API_KEY_QWENEMBEDDING=unused
export FRONTEND_ORIGINS=http://localhost:3000
# leave MEDIA_BASE_URL unset locally so /media serves from the drive

python -m backend.DataBaseFunctions      # creates tables (see 2.7 note); first run downloads the model (~1.2 GB)
```

### 3.3 — Ingest a few videos locally (Section 4 covers the full run)

```bash
# edit processVideo/addNewVideo.py __main__ to point basePath at 2–3 sample video folders on the drive
python -m processVideo.addNewVideo
```

### 3.4 — Run the stack

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000       # terminal 1

cd web && cp .env.example .env.local                          # terminal 2
# .env.local: NEXT_PUBLIC_API_BASE=http://localhost:8000
pnpm install && pnpm dev
```

### 3.5 — Verify

```bash
curl -s localhost:8000/api/videos | head
curl -s localhost:8000/api/filters
curl -s -X POST localhost:8000/inference/ \
  -H 'Content-Type: application/json' \
  -d '{"videoName":"<a real video name>","query":"سؤال تجريبي"}'
```

Then in the browser: `http://localhost:3000` → open a video → video plays and seeks →
ask a question → player jumps to the returned timestamp. Check `/videos/<id>?t=120`
deep-links. Test with an iPhone/Safari if possible (Range-request path).

---

## 4. Phase 2 — build & seed the full database

Run this **locally against the local Postgres** (3.1), not against the cloud DB.
Reason: `add_row()` opens a **new connection per row** (`connectTodatabase()` on every call),
and ingestion inserts one row per InitialChunk + per MergedChunk + per Embedding — tens of
thousands of round trips. Over the internet to Neon that is hours of TLS handshakes; against
localhost it is minutes. Migrate the finished DB afterwards (Section 5.3).

1. Apply code changes 2.3 (the `add_row` Video bug) and 2.7 as needed.
2. Confirm Branch A from Section 1 (transcriptions present). If Branch B, do transcription first.
3. Point `processVideo/addNewVideo.py` `__main__` `basePath` at the drive's `<MainFolder>`
   (the dir whose children are year folders). Keep `transcribe=False`,
   `correctTranscription=False`, `makeSummary=False` unless you have the DeepSeek key and
   want PDFs (needs `weasyprint`, `markdown`, and the Amiri font — 2.8).
4. `python -m processVideo.addNewVideo`
5. Spot-check:

```sql
SELECT count(*) FROM "Video";
SELECT count(*) FROM "Embeddings" WHERE "videoId" IS NULL;   -- must be 0 (the 2.3 bug)
SELECT v.name, count(e.id) FROM "Video" v
  LEFT JOIN "Embeddings" e ON e."videoId" = v.id GROUP BY v.name ORDER BY 2;
```

6. Run a few `/inference/` calls locally and sanity-check the timestamps against the videos.
7. (Optional) books: `python -m processVideo.addNewBook` after fixing `bookIsExist` (2.3).

No vector index is needed: `compute_similarities` filters by `videoId` and scans only that
one video's rows (a few hundred). Do **not** add IVFFlat/HNSW steps.

---

## 5. Phase 3 — provision cloud + migrate

### 5.1 — Cloudflare R2

1. Create bucket, e.g. `es2alsayed-media`.
2. Enable a public access domain (R2 dashboard → Settings → Public Development URL, or
   connect a custom domain like `media.es2alsayed.com`). R2 serves `Range` requests natively.
3. Create an R2 API token (S3 credentials) for uploads.

### 5.2 — Upload media (from the drive)

Use `rclone` (`brew install rclone`, `rclone config` → S3 → provider Cloudflare R2):

```bash
DRIVE="/Volumes/TOSHIBA EXT/Personal/PromptSpeech"
# Upload only what the app serves: mp4, cover.png, and Transcription/*.pdf
rclone copy "$DRIVE" r2:es2alsayed-media \
  --include "*/*/*/*.mp4" \
  --include "*/*/*/cover.png" \
  --include "*/*/*/Transcription/*.pdf" \
  --transfers 8 --progress
```

The R2 key of each object must equal the DB column value. DB values look like
`PromptSpeech/2005/2005-04-25/2005-04-25.mp4` (`{MainFolder}/{Year}/{Video}/...`).
`rclone copy "$DRIVE" r2:bucket` uploads the **contents** of `$DRIVE`, i.e. keys start at
`2005/...` — so either point `rclone` at the parent of `PromptSpeech` **or** set
`MEDIA_BASE_URL` to include the `PromptSpeech` segment. **Verify one URL by hand** before
declaring done:

```bash
# take a real linkToMP4 from the DB, prepend MEDIA_BASE_URL, curl -I it, expect 200 + Accept-Ranges: bytes
```

### 5.3 — Database → managed / VPS Postgres

```bash
# from the local ingest DB
pg_dump -U postgres -h localhost -d SpeechDatabaseInfo -Fc -f es2al.dump

# target: create DB, enable pgvector, restore
psql "<target admin conn string>" -c "CREATE EXTENSION IF NOT EXISTS vector;"
pg_restore --no-owner --no-privileges -d "<target conn string>" es2al.dump
```

Neon: create project (Postgres 16), run the `CREATE EXTENSION` first, then `pg_restore`.
Self-hosted on the VPS: same `pgvector/pgvector:pg16` container as local, with a Docker
volume + a nightly `pg_dump | rclone rcat r2:es2alsayed-backups/…`.

### 5.4 — VPS

1. Hetzner Cloud → Ubuntu 24.04, **CX32 (8 GB)** recommended (CX22/4 GB is the floor and
   leaves little headroom for Next + torch + Postgres together).
2. Install Docker + Docker Compose + Caddy.
3. Point DNS (Cloudflare): `es2alsayed.com` → VPS IP, `media.es2alsayed.com` → R2.

---

## 6. Database size estimate (fill in after Section 1)

Let **H** = total hours of audio (from `du`/duration of the mp4s).

- InitialChunks ≈ `H × 3600 / 30` ≈ `120·H` rows (~30 s each)
- MergedChunks ≈ same order (3-merge / 2-overlap → ~1 merged per initial, minus speaker splits)
- Embeddings: 1 row/merged chunk × `vector(1024)` float32 = **4 KB/row** + text columns

Rough total ≈ **0.6–0.8 MB per hour of audio**
→ 200 h ≈ 120–160 MB, 500 h ≈ 300–400 MB.

Implication: a few hundred hours **fits Neon's free tier (0.5 GB)** and trivially fits a
self-hosted volume. If `du` says the corpus is much larger, or Neon's cold-suspend latency
on the first request is unacceptable, self-host Postgres on the VPS (no suspend, no size
cap, ~$0).

---

## 7. Phase 4 — deploy

### 7.1 — `Dockerfile` (repo root, replaces `backend/Dokcer`) — DONE

`backend/Dokcer` was broken (misnamed; `CMD` used `api.main:app` while the code uses
absolute imports `backend.api.main:app`/`from backend.*`; `COPY . .` from the `backend/`
context put files where `backend.*` couldn't resolve; installed only the incomplete
`requirements.txt`) — it's been deleted. The real one now lives at the **repo root**:
`Dockerfile` (build context = repo root, not `backend/` — the absolute-import layout
requires it). It bakes the embedding model into the image at build time (so container
restarts don't re-download ~1.2 GB) and runs uvicorn with `--proxy-headers
--forwarded-allow-ips=*`, which is what makes the per-IP rate limiting in Section 2.10
key on the real client IP instead of Caddy's — see the comment in the file for why `*` is
safe only because Caddy is the sole route into the container on the compose network.

`.dockerignore` moved from `backend/.dockerignore` to the repo root for the same
build-context reason, and now also excludes `web/node_modules`, `web/.next`, `ASR/`,
`DevAndRes/`, `frontend/` (none of it is needed at runtime) to keep the build context small.

### 7.2 — `docker-compose.yml` (repo root) — DONE

`docker-compose.yml` at the repo root wires up `db` (pgvector), `api` (the `Dockerfile`
above), and `web` (`web/Dockerfile`, multi-stage, `output: "standalone"` — added to
`web/next.config.mjs` — so the runtime image doesn't need `node_modules`). All the
environment values it reads (`${DB_PASSWORD}`, `${MEDIA_BASE_URL}`, etc.) come from an
`.env.production` file you create next to it — see `ENV_VARS.md` (gitignored, not
committed — generate it locally or re-derive it from this doc) for what every variable
means and how to obtain it. Omit the `db` service and point `DB_HOST`/`DB_PORT` at Neon
instead if not self-hosting Postgres.

Run it with: `docker compose --env-file .env.production up -d --build`

### 7.3 — Caddy (`/etc/caddy/Caddyfile`)

```
es2alsayed.com {
    @api path /api/* /inference/* /media/*
    handle @api { reverse_proxy localhost:8000 }
    handle { reverse_proxy localhost:3000 }
}
```

(Drop `/media/*` from `@api` if `MEDIA_BASE_URL` is set — media then never hits the VPS.)
Caddy provisions TLS automatically. Caddy's `reverse_proxy` sets `X-Forwarded-For` by
default — combined with the container's `--proxy-headers` flag (Section 7.1) this is what
makes the per-IP rate limiting (Section 2.10) actually key on the real client IP instead of
`127.0.0.1`. Verify with `curl -s localhost:8000/api/filters -H 'X-Forwarded-For: 1.2.3.4'`
against a request log once deployed.

### 7.4 — Alternative: Next.js on Vercel

Import `web/` (root dir = `web`), set `NEXT_PUBLIC_API_BASE=https://api.es2alsayed.com`,
add `https://<project>.vercel.app` and the prod domain to `FRONTEND_ORIGINS` on the API.
Free for non-commercial use; needs the API on its own public subdomain.

---

## 8. Phase 5 — verify production

- [ ] `curl -I https://media.es2alsayed.com/<real key>` → `200` + `Accept-Ranges: bytes`
- [ ] `https://es2alsayed.com` lists videos, covers load from R2
- [ ] open a video → plays, scrubbing works, works on iOS Safari
- [ ] ask a question → `POST /inference/` returns, player seeks to the segment
- [ ] `/videos/<id>?t=90` deep link starts at 0:90
- [ ] books list + PDF viewer (if books ingested)
- [ ] first request after idle: note latency (model already baked in; Neon cold-resume if used)
- [ ] backup cron: `pg_dump` lands in R2

---

## 9. Cost summary (self-hosted DB + frontend on one VPS)

| Item | Monthly |
|---|---|
| Hetzner CX32 (8 GB) — API + Next + Postgres | ~€7 (~$8) |
| R2 storage — depends on video size, $0.015/GB, **$0 egress** | e.g. 150 GB → ~$2.25 |
| R2 Class A/B operations at this traffic | <$0.10 |
| Cloudflare DNS, Caddy TLS | $0 |
| **Total** | **~$10/month + storage** |

Levers: CX22 (4 GB, €4.5) if it holds under load; Vercel free instead of self-hosting Next;
Neon free tier instead of self-hosted Postgres (adds cold-start latency, 0.5 GB cap, but
removes backup responsibility).

---

## 10. Open questions / risks

1. **Transcriptions on the drive?** (Section 1) — gates the entire effort. Branch B is a
   separate GPU transcription project.
2. **Does a usable DB dump already exist** on the drive? If so, skip Section 4 entirely and
   go straight to `pg_restore` (Section 5.3) — check `find "$DRIVE" -name "*.dump" -o -name "*.sql"`.
3. **`MergedChunks.InitialChunkNumber`** is stored in a `vector`-typed column as a
   stringified list and parsed with `.strip("[]").split(",")` (`InferenceQuery.py:82`).
   `pg_dump -Fc` / `pg_restore` preserves it; a plain-SQL dump round-trip might not — use the
   custom format.
4. **Python 3.11 for ingest** — the 3.14 on this Mac will not install `torch`.
5. **ffmpeg** not installed — needed by `moviepy` if any `.wav` is regenerated during ingest
   (`brew install ffmpeg`).
6. **Model licence / trust_remote_code** — `Qwen/Qwen3-Embedding-0.6B` loads with
   `trust_remote_code=True`; fine, just note it runs vendor code in the image build.
7. **Single box = single point of failure.** Acceptable at this budget; the R2 backup cron
   is the recovery path. Keep the `es2al.dump` from Section 5.3 off-box too.
8. **`next/font/google`** fetches Geist + IBM Plex Arabic at build time — the build host
   needs outbound access to Google Fonts (fine on Hetzner and Vercel).
