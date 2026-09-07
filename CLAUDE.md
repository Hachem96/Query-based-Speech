# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

"Query-based Speech Retrieval" (UI name: **Es2al Sayed / إسأل سيد**) is an RTL Arabic learning platform.
Given a video and a natural-language question, it returns the **start/end timestamp of the segment that
answers the question** and seeks the in-browser video player there. It does **not** generate a text answer —
it is a retrieval/localization system over pre-transcribed, pre-embedded video chunks.

## Running things

Everything uses absolute package imports (`backend.*`, `processVideo.*`, `ASR.*`) and there is no
`setup.py`/`pyproject.toml`, so **always run from the repo root as a module**:

```bash
# Create the PostgreSQL database + schema (needs pgvector; reads DB_* env vars)
python -m backend.DataBaseFunctions

# Ingest videos into the DB (edit the __main__ block for paths first)
python -m processVideo.addNewVideo

# REST API (FastAPI): /inference, /table, /api/* (catalog), /media/* (files)
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Web UI (Dash) — original user-facing app, port 8050
python -m frontend.app

# Web UI (Next.js) — newer frontend, talks to the FastAPI API over HTTP, port 3000
cd web && pnpm install && pnpm dev

# Retrieval-quality evaluation (Precision/Recall/F1/MAP; configure __main__ block)
python -m DevAndRes.Evaluation_Embedding
python -m DevAndRes.Evaluation_Reranker
```

`pip install -r backend/requirements.txt` covers only the API. The full stack additionally needs
`dash`, `dash-bootstrap-components`, `sqlalchemy`, `sentence-transformers`, `torch`, `moviepy`, `Pillow`,
and (for ASR) `transformers`, `pyannote.audio`, `librosa`, `pydub`, `jiwer`. Python 3.11+, FFmpeg, and a
PostgreSQL server with the `pgvector` extension are prerequisites. The Next.js frontend (`web/`) is a
separate Node project — **pnpm** (pinned via `packageManager` in `web/package.json`), Node 18.18+.

There is **no test suite and no linter/formatter config**. Scripts are driven by editing their
`if __name__ == "__main__":` blocks rather than CLI args.

## Configuration (inconsistent — read carefully)

- **Backend** (`backend/*`) reads DB config from env vars: `DB_NAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
  (user is hard-coded to `postgres`).
- **Dash frontend** (`frontend/app.py`) **ignores those** and hard-codes `localhost:5433`, `postgres`/`root`,
  database `SpeechDatabaseInfo`.
- `MAIN_MEDIA_PATH` env var is the root media files are served from — by the Dash app (Flask `/media/<path>`)
  and by the FastAPI app (`backend/api/mediaAPI.py`, `/media/{path}`, with `Range`/`206` support for video
  seeking); `Video`/`Book` path columns in the DB are stored relative to it.
- **FastAPI CORS**: `FRONTEND_ORIGINS` env var (comma-separated, default `http://localhost:3000`) — the
  Next.js frontend's origin must be listed here.
- **Next.js frontend** (`web/`) config: `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`) in
  `web/.env.local`, read on both server and client.
- External API keys via env vars: `API_KEY_DEEPSEEK` (transcription correction, `processVideo/create_pdf.py`),
  `Qwen_API_KEY` / `API_KEY_QWENEMBEDDING` (Qwen embedding API — currently only used by the unused API code
  paths; the active path uses a local model).

## Architecture

### Data model (PostgreSQL + pgvector)

All tables are created by `backend/DataBaseFunctions.py:creat_db_tables()` (column names/types are defined
inline there). The chunk hierarchy is the core idea:

- **`Video`** — metadata + file-path columns (`linkToMP4`, `linkToCover`, `linkToPdf`, `linkToSummaryPdf`,
  `linkToTranslation`, transcription paths).
- **`InitialChunks`** — raw transcription segments (~30 s each) with `startTimeStamp`, `endTimeStamp`,
  `speaker`, and a per-video sequential `number`.
- **`MergedChunks`** — a sliding window over InitialChunks (`nbChunksToMerge=3`, `nbOverlapChunks=2`),
  **split whenever the speaker changes**. `InitialChunkNumber` holds the list of constituent InitialChunk
  numbers — stored abusing a `vector` column type.
- **`Embeddings`** — one row per MergedChunk; column `Qwen-0.6B` is a `vector(1024)` from
  `Qwen/Qwen3-Embedding-0.6B` (normalized). Schema anticipates multiple embedding models but only one is live.
- **`Book`** — standalone book metadata (browsed/viewed as PDFs; not part of retrieval).

### Retrieval pipeline — `backend/InferenceQuery.py:inference_query(query, videoName)`

1. Embed the query with `backend/embedding.py:embed_query` (local SentenceTransformer, L2-normalized).
2. `backend/searchinDatabase.py:compute_similarities` — pgvector `<#>` (negative inner product) between the
   query vector and all `Embeddings` rows for that `videoId`.
3. Sort **ascending** (because `<#>` is negated, smaller = more similar), take `topK = 25`.
4. `getSegmentTopK` grows the rank-1 merged chunk into a contiguous run of neighboring high-ranked chunks,
   tolerating single-chunk gaps (`oneHole = True`).
5. Map selected MergedChunks → their InitialChunk numbers → look up `startTimeStamp`/`endTimeStamp` of the
   first and last → return `{startTimeStamp, endTimeStamp, duration}`.

### Subsystems

- **`backend/`** — retrieval logic + FastAPI wrapper. `api/main.py` mounts `api/inferenceAPI.py` (`/inference`),
  `api/getTableInfoAPI.py` (`/table`, generic/legacy), `api/catalogAPI.py` (`/api/videos`, `/api/videos/{id}`,
  `/api/books`, `/api/books/{id}`, `/api/filters` — camelCased JSON, file paths as `/media` URLs), and
  `api/mediaAPI.py` (`/media/{path}`). `api/db.py` holds the shared psycopg2 connection + `to_media_url()`.
  `embedding.py` and `searchinDatabase.py` also contain their own `connectTodatabase()` copies.
- **`frontend/`** — Dash single-page app (URL-routed views: video list, video player + Q&A chat, books).
  **It imports `inference_query` directly rather than calling the API.** `app.py` is current; `appV2.py` is
  an older variant (mock answers, `HH:MM:SS` formatting) — do not edit it expecting it to be live.
- **`web/`** — Next.js (App Router, TypeScript, pnpm) frontend, RTL Arabic. Same views as the Dash app but
  **consumes the FastAPI API over HTTP** (`web/lib/api.ts`) — no Python imports. Server components fetch the
  catalog; `web/components/VideoWatch.tsx` (client) calls `POST /inference/` and seeks the `<video>` to the
  result. Deep link `/videos/{id}?t=SECONDS`. The Dash app is untouched and still runs in parallel.
- **`processVideo/`** — ingestion pipeline (`addNewVideo.py`): mp4→wav, generate cover image, transcribe,
  LLM-correct transcript + render PDF, merge chunks, embed, write every stage to the DB. Expects a directory
  layout of `<MainFolder>/<Year>/<VideoName>/<VideoName>.mp4` plus `caption.txt`. `common.py` holds the
  mp4→wav and chunk-merging helpers; `embedding.py` here is a **separate copy** from `backend/embedding.py`
  with extra API-based variants.
- **`ASR/SpeechTextConversion.py`** — Whisper `large-v3` + `pyannote/speaker-diarization-3.1` transcription.
  Note: `addNewVideo.py`'s import of `transcribe_One_Speech` is currently commented out, so ingestion only
  works with `transcribe=False` (consuming a pre-existing `Transcription/` folder).
- **`DevAndRes/`** — offline research scripts: prepare evaluation embeddings, then score embedding/reranker
  models with Precision/Recall/F1/MAP. `ExportVideoApp.py` exports app data. `test.ipynb` is gitignored.

## Gotchas

- `backend/embedding.py` and `processVideo/embedding.py` are near-duplicates that drift; changing embedding
  behavior means touching both.
- Both `embedding.py` files construct `OpenAI(api_key=os.getenv(...))` at **module import time**. The openai
  v1.x SDK raises if the key resolves to `None`, so `Qwen_API_KEY` (backend) / `API_KEY_QWENEMBEDDING`
  (processVideo) must be set to *something* just to import `backend.embedding` — which `InferenceQuery`, the
  API, and the Dash app all pull in transitively. This is the most likely first-run failure.
- **Ingestion (`processVideo.addNewVideo`) is currently broken in two places** for new videos:
  (a) the `transcribe_One_Speech` import from `ASR` is commented out (so only `transcribe=False` works), and
  (b) `add_row("Video", ...)` enters a `table_name == "Video"` branch that calls
  `videoIsExist(configuration, videoName)` with an undefined `configuration` and the wrong arity; the bare
  `except Exception` swallows it and returns `None`, so `videoId` is `None` and every child
  `InitialChunks`/`MergedChunks`/`Embeddings` row gets a null foreign key.
- `backend/README.md` references a Dockerfile named `Dokcer`; only `backend/.dockerignore` exists in the repo.
