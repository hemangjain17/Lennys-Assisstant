"""
Phase 6: FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import sessions, chat, artifacts

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lenny Growth Assistant API",
    description="RAG-powered podcast knowledge assistant using Lenny's Podcast transcripts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow both local development origins and wildcard/configured live origins
allowed_origins = [settings.frontend_origin] if settings.frontend_origin else []
if "localhost" in settings.frontend_origin:
    # Add wildcard or fallback for Vercel production hosting to bypass CORS preflights
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment != "production" else allowed_origins,
    allow_credentials=True if settings.environment == "production" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(artifacts.router, prefix="/api/v1")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/v1/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.environment,
        "embedding_model": settings.embedding_model,
        "llm_model": settings.gemini_model_name,
    }


@app.get("/", tags=["root"])
async def root():
    return {"message": "Lenny Growth Assistant API", "docs": "/docs"}
