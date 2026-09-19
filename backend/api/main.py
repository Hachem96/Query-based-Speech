import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

load_dotenv()

from backend.api.inferenceAPI import router as inference_router
from backend.api.catalogAPI import router as catalog_router
from backend.api.db import MEDIA_BASE_URL
from backend.api.limiter import limiter

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# The Next.js frontend calls the API cross-origin; its origin(s) must be listed
# here. Comma-separated ``FRONTEND_ORIGINS`` env var, default localhost:3000.
origins = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register the routers
app.include_router(inference_router, prefix="/inference", tags=["Inference"])
app.include_router(catalog_router, prefix="/api", tags=["Catalog"])

# ``media_router`` serves files from MAIN_MEDIA_PATH with Range support and
# competes with the embedding model for CPU/bandwidth on the same box. Once
# MEDIA_BASE_URL points at object storage (R2), video/cover/PDF bytes never
# hit this process, so the proxy route is dropped entirely.
if not MEDIA_BASE_URL:
    from backend.api.mediaAPI import router as media_router
    app.include_router(media_router, prefix="/media", tags=["Media"])
