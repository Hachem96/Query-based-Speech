# Deployment Plan — Es2al Sayed / إسأل سيد

Scope: deploy the **Next.js** frontend (`web/`) + **FastAPI** backend (`backend/`) publicly on
**Alibaba Cloud**. We build and seed the PostgreSQL + pgvector database from the videos on the
external drive, and host all media (mp4 / covers / PDFs) on **Alibaba Cloud OSS**.

Last revised 2026-09-25. Anything that can't be checked from the repo (the drive contents,
Alibaba prices and regional service availability) is marked **VERIFY**. Don't skip those.

---

## 0. Decisions & architecture

### 0.1 — Region: pick an international region, NOT mainland China

This decision comes before everything else. A **mainland-China** region (Hangzhou, Beijing,
Shanghai, …) breaks this stack in four ways:

- **ICP filing (备案)** is required before a domain can serve on ports 80/443, and before a
  custom domain can be bound to OSS or CDN. That takes weeks and needs a Chinese entity.
- **Hugging Face is blocked.** The `Dockerfile` downloads `Qwen/Qwen3-Embedding-0.6B` at build time, so the build fails.
- **Docker Hub** is slow or unreliable, and so is PyPI without a mirror.
- **`next/font/google`** can't reach Google Fonts at build time, so `pnpm build` fails.

**Recommended: Middle East — Riyadh (`me-central-1`) or Dubai (`me-east-1`)**, because it is
closest to the Arabic-speaking audience. Frankfurt (`eu-central-1`) or Singapore
(`ap-southeast-1`) are fallbacks. **VERIFY** before committing that the chosen region offers
ECS, OSS with custom domains, CDN, and (if you want it) ApsaraDB RDS for PostgreSQL. Put
**every resource in the same region**, so ECS↔OSS traffic can use the free internal endpoint.

### 0.2 — Stack

| Layer | Choice | Notes |
|---|---|---|
| Object storage (mp4, covers, PDFs) | **OSS** bucket, public-read, served on a **custom domain** `media.es2alsayed.com` (optionally fronted by **Alibaba Cloud CDN**) | A custom domain is **mandatory**, see 5.2. **Egress is billed per GB**, see Section 9. |
| Compute | **One ECS instance**, Ubuntu 24.04, **≥ 8 GB RAM** (e.g. 2 vCPU / 8 GB general-purpose `g`-family `.large`, or 4 vCPU / 8 GB) | Runs API + Next + Postgres + Caddy via Docker Compose. The embedding model needs ~1.5 GB resident. |
| Database (Postgres 16 + pgvector) | **Self-hosted on the ECS box** (`pgvector/pgvector:pg16` container), nightly `pg_dump` → OSS | Alternative: **ApsaraDB RDS for PostgreSQL**. It supports pgvector but needs code changes, see 5.5. |
| Frontend (Next.js 15 SSR) | Same ECS box, `web/Dockerfile` (standalone output) | |
| TLS / reverse proxy | **Caddy** container, auto-HTTPS | |
| DNS | **Alibaba Cloud DNS** (or keep your current registrar's DNS) | `es2alsayed.com` → ECS EIP, `media.es2alsayed.com` → CNAME to the OSS/CDN domain. |

```
                      ┌──────────── ECS instance (one box) ───────────────┐
   browser  ──HTTPS──▶│  caddy :443                                       │
                      │    ├── /  , /videos/* , /books/*  ─▶ web:3000     │
                      │    └── /api/* , /inference/*       ─▶ api:8000    │
                      │                                        │          │
                      │  db (Postgres+pgvector, :5432 internal) ◀┘         │
                      └───────────────────────────────────────────────────┘
   <video>/<img>/<iframe> ──HTTPS──▶ media.es2alsayed.com ─▶ (CDN) ─▶ OSS bucket
```

The API only serves inference and catalog JSON. Media bytes go **straight from OSS/CDN** to the
browser (`MEDIA_BASE_URL` set, see 2.1), so the ECS disk and CPU never touch video files.

---

## 1. STOP — verify transcriptions exist before anything else

`processVideo/addNewVideo.py:2` has the ASR import commented out. That means only
`transcribe=False` works, and that path **requires a pre-existing transcription JSON per video** at
`<video folder>/Transcription/transcription_whisper_large_v3.json`.

**VERIFY (mount the TOSHIBA drive first):**

```bash
DRIVE="/Volumes/TOSHIBA EXT/Personal/PromptSpeech"
find "$DRIVE" -name "*.mp4" | wc -l
find "$DRIVE" -name "transcription_whisper_large_v3.json" | wc -l
find "$DRIVE" -name "caption.txt" | wc -l
du -sh "$DRIVE"
find "$DRIVE" -maxdepth 3 -type d | head -30   # expect <MainFolder>/<Year>/<VideoName>/
find "$DRIVE" -name "*.dump" -o -name "*.sql"  # an existing DB dump lets you skip Section 4
```

- **Branch A — the mp4 and transcription counts roughly match:** ingestion is a straight run
  (Section 4). Continue with this plan.
- **Branch B — the transcription count is ~0:** this is a transcription project first, not a
  deployment task. You'd run Whisper `large-v3` + `pyannote/speaker-diarization-3.1` (a gated HF
  model) over the whole corpus on a rented GPU. That code path has **never run end to end** in
  this repo. Budget days, not hours.

Record the numbers. They size the database (Section 6) and the OSS bill (Section 9).

---

## 2. Code status

### 2.1 — Already done

| Change | Where |
|---|---|
| `main.py` mounts `/inference`, `/api` (catalog) with CORS (`FRONTEND_ORIGINS`); `/table` (SQL-injectable table/column read) is **not** mounted | `backend/api/main.py` |
| Media URLs point at object storage when `MEDIA_BASE_URL` is set. The `/media` proxy is only registered when it's **unset** (local dev). The frontend passes absolute URLs through unchanged. | `backend/api/db.py:to_media_url`, `web/lib/api.ts:mediaUrl` |
| `add_row("Video")` bug removed (it gave every child row a `NULL` `videoId`) | `backend/DataBaseFunctions.py` |
| `requirements.txt` complete: `sentence-transformers==6.0.1`, `torch==2.4.1` (CPU wheels), `slowapi` | `backend/requirements.txt` |
| DB-connection leak in `/inference` fixed. Errors no longer leak `str(e)`. An unknown `videoName` returns 404. Symlink bypass of the media path guard fixed (`realpath`). | `backend/InferenceQuery.py`, `backend/api/*` |
| Rate limiting: `/inference` 10/min, `/api/*` 60/min, `/media/*` 120/min per client IP. `query`/`videoName` length caps. | `backend/api/limiter.py` |
| Real client IP behind the proxy: uvicorn runs with `--proxy-headers --forwarded-allow-ips=*` | `Dockerfile` |
| Security headers + CSP | `web/next.config.mjs` |
| Root `Dockerfile` (model baked into the image), `web/Dockerfile` (standalone), `docker-compose.yml`, root `.dockerignore` | repo root |
| Committed secrets removed from the working tree | see 2.5 |

### 2.2 — CSP allows the media origin — DONE

The CSP in `web/next.config.mjs` had no `frame-src`, so it fell back to `default-src 'self'`.
That blocked the book viewer's PDF `<iframe>` (`web/app/books/[id]/page.tsx`) from the media
domain. It also blocked local dev, where covers, video and PDFs come from `http://localhost:8000`
and `https:`-only rules don't cover that. `img-src`, `media-src` and the new `frame-src` now also
allow `NEXT_PUBLIC_API_BASE` and `MEDIA_BASE_URL`. Headers are computed at **build time**, so
`MEDIA_BASE_URL` is also a build arg of `web/Dockerfile` (compose passes it). Rebuild `web` if the
media domain changes.

### 2.3 — Caddy in `docker-compose.yml` — DONE

`docker-compose.yml` had no proxy and no published ports, so nothing was reachable from outside.
It now has a `caddy` service (`caddy:2`, ports 80/443, config in the repo-root `Caddyfile`, certs
persisted in the `caddy_data` volume). It is the **only** service with published ports. The
API's `--forwarded-allow-ips=*` is only safe if Caddy is the sole route to it, so **never add
`ports:` to `api`, `web` or `db`.**

Caddy also gets a network alias equal to `SITE_DOMAIN`. Next's server components fetch the
catalog from `NEXT_PUBLIC_API_BASE` (`https://es2alsayed.com`). Without the alias, those SSR
fetches would leave the box to the EIP and come back in, which may not work on ECS (hairpin NAT)
and would put all SSR traffic in one rate-limit bucket. With it, containers resolve the domain
straight to Caddy, and the TLS cert still matches.

### 2.4 — Needs only an env var, not code

- **`Qwen_API_KEY`** must be set to any non-empty string (e.g. `unused`).
  `backend/embedding.py` builds an OpenAI client at import time, and the SDK raises on `None`.
  Set the same for `API_KEY_QWENEMBEDDING` when running `processVideo/`.
- **`MEDIA_BASE_URL=https://media.es2alsayed.com`** in production. Leave it unset locally.

### 2.5 — REQUIRED before going public: rotate leaked credentials

The DeepSeek key and the Telegram `api_id`/`api_hash`/phone were removed from the current files,
but **they are still in git history** (`git log -p -S '7b01d9b55b6b7adcf14446a017e46d20'`).

- Revoke the DeepSeek key and issue a new one.
- Reset the Telegram app credentials at my.telegram.org. Treat the phone number as exposed.
- If the repo will be public, run `git filter-repo`. It rewrites history and breaks existing clones.
- No Telethon `.session` file was ever committed (checked).

### 2.6 — Optional

- **`DB_USER`:** `user="postgres"` is hard-coded in five `psycopg2.connect` calls
  (`backend/api/db.py`, `backend/InferenceQuery.py`, `backend/searchinDatabase.py`, 2×
  `backend/DataBaseFunctions.py`). That's fine for self-hosted Postgres. It's **required** if you
  use ApsaraDB RDS (5.5).
- **Cover font:** `processVideo/common.py:7` hard-codes a `/mnt/d/...Amiri-Bold.ttf` path. Without
  it, covers can't render Arabic. Make it an env var if covers matter; the catalog works with `coverUrl: null`.
- **Books ingest:** `processVideo/addNewBook.py` calls `bookIsExist(title, author)` against a
  3-parameter signature. Fix it only if you ingest books.

### 2.7 — Abuse surface: what's true and what isn't

- This is a public, unauthenticated app with one CPU-expensive endpoint (`/inference`). Rate limiting
  is the real protection. Once deployed, verify it keys on the client IP, not the proxy: fire 11
  quick `/inference` calls from two different networks, and only the noisy one should get 429s.
- **"Watch, not download" can't be enforced** for a plain `<video src>`. Anything the browser can
  play, the user can save. The only realistic options add friction: short-lived **OSS presigned URLs**
  (re-signed per page load, which means a code change in `to_media_url`) or HLS segmentation.
  Don't claim download protection in user-facing copy.
- Re-check the CSP if you add any third-party script or embed.

---

## 3. Phase 1 — local setup & test (on this Mac)

Prereqs: Docker ✓, pnpm ✓, node ✓, **ffmpeg ✗** (`brew install ffmpeg`), and **Python 3.11**
(`brew install python@3.11`). The system Python 3.14 has no torch wheels.

```bash
# 3.1 Postgres + pgvector (use :pg15 instead if you plan on ApsaraDB RDS — see 5.5)
docker run -d --name espg -p 5432:5432 \
  -e POSTGRES_PASSWORD=root -e POSTGRES_DB=SpeechDatabaseInfo pgvector/pgvector:pg16
docker exec -it espg psql -U postgres -d SpeechDatabaseInfo -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3.2 Backend venv + env
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
export DB_NAME=SpeechDatabaseInfo DB_PASSWORD=root DB_HOST=localhost DB_PORT=5432
export MAIN_MEDIA_PATH="/Volumes/TOSHIBA EXT/Personal/PromptSpeech"
export Qwen_API_KEY=unused API_KEY_QWENEMBEDDING=unused
export FRONTEND_ORIGINS=http://localhost:3000
# MEDIA_BASE_URL unset locally → /media proxy serves from the drive
python -m backend.DataBaseFunctions        # creates tables; first run downloads the model (~1.2 GB)

# 3.3 Ingest 2–3 sample videos (edit basePath in processVideo/addNewVideo.py __main__)
python -m processVideo.addNewVideo

# 3.4 Run
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000                 # terminal 1
cd web && cp .env.example .env.local && pnpm install && pnpm dev        # terminal 2
```

**Verify:**

```bash
curl -s localhost:8000/api/videos | head
curl -s -X POST localhost:8000/inference/ -H 'Content-Type: application/json' \
  -d '{"videoName":"<a real video name>","query":"سؤال تجريبي"}'
```

Then in the browser, open a video: it should play and seek. Ask a question: the player should
jump to the returned segment. `/videos/<id>?t=120` should deep-link. Try it in Safari too.

---

## 4. Phase 2 — build & seed the full database (locally)

Ingest against the **local** Postgres, not the cloud one. `add_row()` opens a new connection per
row, which means tens of thousands of round trips. Migrate the finished DB afterwards (5.5).

1. Confirm Branch A (Section 1).
2. Point `basePath` in `processVideo/addNewVideo.py` `__main__` at the drive's `<MainFolder>`
   (the dir whose children are year folders). Keep `transcribe=False`,
   `correctTranscription=False`, `makeSummary=False` unless you have a (new) DeepSeek key and want PDFs.
3. `python -m processVideo.addNewVideo`
4. Spot-check:

   ```sql
   SELECT count(*) FROM "Video";
   SELECT count(*) FROM "Embeddings" WHERE "videoId" IS NULL;   -- must be 0
   SELECT v.name, count(e.id) FROM "Video" v
     LEFT JOIN "Embeddings" e ON e."videoId" = v.id GROUP BY v.name ORDER BY 2;
   ```

5. Run a few `/inference/` calls and sanity-check the timestamps against the videos.

No vector index is needed: `compute_similarities` scans only one video's rows (a few hundred).

---

## 5. Phase 3 — provision Alibaba Cloud + migrate

### 5.1 — Account & access

1. Create the Alibaba Cloud (international) account and complete real-name verification.
2. In **RAM**, create a user for uploads/backups with an AccessKey scoped to the media and
   backup buckets only (e.g. the `AliyunOSSFullAccess` policy, or a custom bucket-scoped policy).
   Don't use the root account's AccessKey.

### 5.2 — OSS bucket for media

1. Create bucket `es2alsayed-media` in the chosen region, Standard storage class.
2. **Public access:** new buckets have **Block Public Access** on. Turn it off for this bucket,
   then set the ACL to **public-read**, or add a bucket policy granting anonymous `oss:GetObject`.
   Keep it **not** public-write.
3. **Custom domain is mandatory.** Browser requests to the default
   `<bucket>.oss-<region>.aliyuncs.com` domain get `Content-Disposition: attachment` +
   `x-oss-force-download: true` in **all regions**. PDFs would download instead of rendering in
   the iframe. So:
   - Bucket → **Domain Names** → map `media.es2alsayed.com` (or map it on **CDN** with the bucket
     as origin, which is recommended for video, see Section 9).
   - Add the CNAME record it gives you in DNS.
   - Attach an **HTTPS certificate** (a free DV cert from Certificate Management Service, or
     upload your own). The CSP only allows `https:` media.
4. **CORS:** not needed for `<video>`, `<img>` or `<iframe>`. Add a GET rule for
   `https://es2alsayed.com` only if the frontend ever `fetch()`es media.
5. Optionally turn on **hotlink protection** (Referer whitelist `es2alsayed.com`, allow empty
   Referer for iOS media players). It adds friction but doesn't prevent downloads.

### 5.3 — Upload media from the drive

Use Alibaba's **`ossutil`** CLI (install it from the OSS docs, then run `ossutil config` with
the RAM AccessKey and the region endpoint `oss-<region>.aliyuncs.com`; see `ENV_VARS.md` §4).
Upload only what the app serves: mp4, covers and PDFs.

```bash
DRIVE="/Volumes/TOSHIBA EXT/Personal/PromptSpeech"
ossutil cp -r "$DRIVE/" oss://es2alsayed-media/PromptSpeech/ \
  --include "*.mp4" --include "cover.png" --include "*.pdf" \
  --update        # skip objects already uploaded, so an interrupted run can be resumed
```

`ossutil` 1.x and 2.x differ slightly in flag names, so check `ossutil help cp` for your version.
Uploading hundreds of GB from a home connection takes a long time. Run it inside `tmux`/`screen`
and rerun it with `--update` if it drops.

**Key alignment:** each object key must equal the DB path after `to_media_url()` strips
`MAIN_MEDIA_PATH`. The command above produces keys like
`PromptSpeech/2005/2005-04-25/2005-04-25.mp4`. Run `SELECT "linkToMP4" FROM "Video" LIMIT 1;`,
and set `MAIN_MEDIA_PATH` in production to whatever comes **before** `PromptSpeech/` in that
value (empty if the DB value already starts with `PromptSpeech/`). **Verify one URL by hand:**

```bash
# take a real linkToMP4 from the DB → build the URL the API would return → then:
curl -I "https://media.es2alsayed.com/<key>"          # expect 200, Accept-Ranges: bytes, no Content-Disposition: attachment
curl -I -H 'Range: bytes=0-1' "https://media.es2alsayed.com/<key>"   # expect 206
```

### 5.4 — ECS instance

1. Create the ECS instance: Ubuntu 24.04, **≥ 8 GB RAM** (4 GB is too tight for torch + Next +
   Postgres). A 40–60 GB ESSD system disk is enough, since media lives on OSS and the rest is
   Docker images (torch is several GB) plus the DB.
   - Billing: **pay-by-traffic** public bandwidth is fine, because only HTML/JSON leaves the box.
     Attach an **EIP** so the IP survives instance changes.
   - Cheaper alternative: **Simple Application Server** with an 8 GB plan, if offered in the region.
     **VERIFY** the price.
2. **Security group:** inbound **22** (your IP only), **80**, **443**. Never open **5432**, 8000 or 3000.
3. Install Docker Engine + the Compose plugin. Clone the repo and create `.env.production`
   (see `ENV_VARS.md`).
4. DNS: `es2alsayed.com` A-record → EIP. `media.es2alsayed.com` CNAME → OSS/CDN (5.2).

### 5.5 — Database → ECS (default) or ApsaraDB RDS

```bash
# from the local ingest DB — custom format (preserves the vector-typed InitialChunkNumber column)
pg_dump -U postgres -h localhost -d SpeechDatabaseInfo -Fc -f es2al.dump
```

**Self-hosted on ECS (default).** Start just the DB with
`docker compose --env-file .env.production up -d db`. Without the env file `DB_PASSWORD` is empty
and the container refuses to initialise. Then copy
the dump into the container and restore:

```bash
docker compose exec db psql -U postgres -d SpeechDatabaseInfo -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose cp es2al.dump db:/tmp/es2al.dump
docker compose exec db pg_restore -U postgres -d SpeechDatabaseInfo --no-owner --no-privileges /tmp/es2al.dump
```

Nightly backup to a **separate private** bucket `es2alsayed-backups`, over the **internal**
endpoint (`oss-<region>-internal.aliyuncs.com`, where same-region traffic is free). Use a
lifecycle rule to expire old dumps after about 30 days. On the ECS box, run `ossutil config`
with the `-internal` endpoint, then:

```cron
0 3 * * * cd /opt/es2alsayed && docker compose exec -T db pg_dump -U postgres -Fc SpeechDatabaseInfo > /tmp/es2al.dump && ossutil cp -f /tmp/es2al.dump oss://es2alsayed-backups/es2al-$(date +\%F).dump && rm /tmp/es2al.dump
```

Also enable an **ECS automatic snapshot policy** on the system disk (Postgres volume included)
as a second recovery path.

**ApsaraDB RDS for PostgreSQL (alternative).** It's managed and has backups built in, but costs
more than running Postgres on the ECS box. Caveats:

- pgvector is documented for **PG 14/15+** (minor engine ≥ 20230430). **VERIFY** which majors
  your region offers. Dump from a matching local major (`pgvector/pgvector:pg15` in 3.1) to avoid
  `pg_restore` version friction.
- The account name `postgres` is almost certainly reserved, so thread a **`DB_USER` env var**
  through the five connect calls (2.6).
- `DataBaseFunctions.create_database()` issues `CREATE DATABASE` and won't work there. Create
  the DB in the console, run `CREATE EXTENSION vector;` as the privileged account, then `pg_restore`.
- Put it in the same VPC as ECS, whitelist only the ECS private IP, and set `DB_HOST` to the
  internal endpoint. Drop the `db` service from compose.

---

## 6. Database size estimate (fill in after Section 1)

Let **H** = total hours of audio.

- InitialChunks ≈ `120·H` rows (~30 s each). MergedChunks are about the same.
- Embeddings: one `vector(1024)` float32 per merged chunk, ≈ 4 KB/row.

That's ≈ **0.6–0.8 MB per hour of audio** (200 h ≈ 120–160 MB). It fits trivially on the ECS disk.

---

## 7. Phase 4 — deploy

### 7.1 — Images (done)

- The root **`Dockerfile`** builds the API from the repo root (absolute `backend.*` imports) and bakes
  the embedding model into the image. It needs Hugging Face access at build time, see 0.1.
- **`web/Dockerfile`** is multi-stage with `output: "standalone"`. `NEXT_PUBLIC_API_BASE` is inlined
  **at build time**, so set it to `https://es2alsayed.com` (same origin, via Caddy) before building.
  Rebuild if it changes.

### 7.2 — `.env.production`

Minimum values (full reference: `ENV_VARS.md`, gitignored):

```dotenv
SITE_DOMAIN=es2alsayed.com
DB_PASSWORD=<strong random>
MAIN_MEDIA_PATH=<prefix to strip, see 5.3>
MEDIA_BASE_URL=https://media.es2alsayed.com
FRONTEND_ORIGINS=https://es2alsayed.com
NEXT_PUBLIC_API_BASE=https://es2alsayed.com
Qwen_API_KEY=unused
```

`SITE_DOMAIN`, `FRONTEND_ORIGINS` and `NEXT_PUBLIC_API_BASE` must all name the same domain.

### 7.3 — `Caddyfile` (repo root) — DONE

It serves `{$SITE_DOMAIN}`, sends `/api/*` and `/inference/*` to `api:8000` and everything else
to `web:3000`, and gzip/zstd-compresses responses. Media isn't proxied, because browsers fetch it
straight from the OSS/CDN domain. Caddy gets the TLS cert automatically once DNS points at the
EIP and ports 80/443 are open. `reverse_proxy` sets `X-Forwarded-For`, which uvicorn trusts (7.1).

### 7.4 — Bring it up

```bash
docker compose --env-file .env.production up -d --build
docker compose logs -f api   # model load + first request
```

---

## 8. Phase 5 — verify production

- [ ] `curl -I https://media.es2alsayed.com/<real key>` → `200`, `Accept-Ranges: bytes`, **no** `Content-Disposition: attachment`
- [ ] `https://es2alsayed.com` lists videos, covers load from the media domain
- [ ] Open a video: it plays, scrubbing works, and it works on iOS Safari
- [ ] Ask a question: `POST /inference/` returns and the player seeks to the segment
- [ ] `/videos/<id>?t=90` deep link starts at 1:30
- [ ] Book PDF renders **inline** in the iframe (needs the custom domain, 5.2)
- [ ] `docker compose exec web node -e "fetch('https://es2alsayed.com/api/filters').then(r=>console.log(r.status))"` → `200` (SSR path, see 2.3)
- [ ] Rate limit: 11 rapid `/inference` calls → 429 for that client only
- [ ] `nmap`/port check from outside: only 22/80/443 open
- [ ] Backup cron: a dump lands in `es2alsayed-backups`, and a test `pg_restore` of it works

---

## 9. Cost model

**VERIFY every number on the Alibaba pricing pages for your region.** Prices differ by region
and change often.

| Item | Driver | Notes |
| --- | --- | --- |
| ECS (8 GB) + EIP + 40–60 GB ESSD | fixed monthly | The largest fixed cost. Subscription (monthly/yearly) is cheaper than pay-as-you-go. |
| ECS outbound traffic | HTML/JSON only | Small. |
| OSS storage | `du -sh` of uploaded media × per-GB-month | Standard class. |
| **Media egress** | **views × MB watched per view** | **The dominant variable cost.** OSS internet egress is billed per GB. Serving through **Alibaba CDN** (OSS as origin) is usually cheaper per GB than direct OSS egress, and CDN resource plans cut it further. |
| OSS requests | GET count | Negligible at this scale. |
| Backups bucket | a few hundred MB × 30 days | Negligible. Internal-endpoint upload is free. |
| Certificate, DNS | | Free DV cert / basic DNS tier. |

Back-of-envelope for egress: 1,000 views/month × ~150 MB watched ≈ 150 GB/month. Multiply by your
region's CDN per-GB price. Levers: CDN resource plans, lower-bitrate transcodes (e.g. 480p
H.264 for talks, which cuts GB watched by 2–4×), and hotlink protection against bandwidth leeching.

---

## 10. Open questions / risks

1. **Transcriptions on the drive?** (Section 1) This gates the whole effort.
2. **Region choice** (0.1): confirm service availability and pricing before creating resources.
   Moving later means re-uploading all media.
3. **Egress cost is uncapped.** Set a **budget alert** in Billing, and consider CDN bandwidth caps /
   usage alerts, so a viral or scraped video can't produce a surprise bill.
4. **`MergedChunks.InitialChunkNumber`** is a stringified list in a `vector` column. Use `pg_dump -Fc`
   (custom format), not a plain-SQL round trip.
5. **Model licence / `trust_remote_code=True`**: the image build runs vendor code from `Qwen/Qwen3-Embedding-0.6B`.
6. **Single box = single point of failure.** That's acceptable at this budget. Recovery is the OSS
   backups plus an ECS snapshot policy. Keep `es2al.dump` off-box too.
7. **Build-time network:** the API image needs Hugging Face and PyPI (+ the PyTorch CPU index), and
   the web image needs npm + Google Fonts. All are fine from international regions.
