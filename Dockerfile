# Backend (FastAPI + local embedding model) image. Build from the REPO ROOT
# (not backend/), since the code uses absolute imports (backend.*, processVideo.*):
#   docker build -f Dockerfile -t es2alsayed-api .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HOME=/models

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Bake the embedding model into the image so container restarts don't
# re-download ~1.2 GB from Hugging Face on every deploy.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('Qwen/Qwen3-Embedding-0.6B', trust_remote_code=True)"

COPY backend/ ./backend/
# InferenceQuery imports backend.* only; processVideo/ASR/frontend are not
# needed at runtime and are intentionally not copied.

EXPOSE 8000
# --proxy-headers + --forwarded-allow-ips trusts X-Forwarded-For from Caddy
# (its container on the compose network) so slowapi's per-IP rate limiting
# (backend/api/limiter.py) keys on the real client IP, not Caddy's address.
# If this container is ever exposed directly to the internet without Caddy
# in front, remove these flags or pin forwarded-allow-ips to Caddy's IP.
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
