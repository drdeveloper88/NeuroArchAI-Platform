"""NeoArchAI - Application Entry Point

Launches the FastAPI server with:
  - REST API  at  /api/...
  - Static UI at  /
  - API docs  at  /docs  (Swagger) and /redoc
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("neoarchai")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NeoArchAI",
    description=(
        "Agentic House Architecture Design System powered by LangGraph + CrewAI.\n\n"
        "Generates complete designs at three levels:\n"
        "1. **Basic Design** – Room schedule, materials, cost estimate\n"
        "2. **2D Layout** – Professional architectural floor plans (PNG + SVG)\n"
        "3. **3D Model** – Interactive Plotly 3D visualization (HTML)\n\n"
        "All free – uses Groq (free tier) or Ollama (local) as LLM backend."
    ),
    version="1.0.0",
    contact={
        "name":  "NeoArchAI",
        "url":   "https://github.com/neoarchai",
        "email": "hello@neoarchai.ai",
    },
    license_info={"name": "MIT"},
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api")

# ── Static files ──────────────────────────────────────────────────────────────
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
    """Serve the main UI."""
    return FileResponse(str(static_dir / "index.html"))


# ── Startup / Shutdown events ─────────────────────────────────────────────────

@app.on_event("startup")
async def _startup():
    from config import (
        OUTPUT_DIR, LLM_PROVIDER, LLM_MODEL,
        GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY,
        TOGETHER_API_KEY, COHERE_API_KEY, OPENAI_COMPAT_BASE_URL,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _key_map = {
        "groq": bool(GROQ_API_KEY),
        "gemini": bool(GEMINI_API_KEY),
        "openai": bool(OPENAI_API_KEY),
        "together": bool(TOGETHER_API_KEY),
        "cohere": bool(COHERE_API_KEY),
        "ollama": True,
        "openai-compat": bool(OPENAI_COMPAT_BASE_URL),
        "none": False,
    }
    llm_ready = _key_map.get(LLM_PROVIDER, False)
    logger.info("=" * 60)
    logger.info("NeoArchAI started")
    logger.info("  LLM Provider : %s", LLM_PROVIDER)
    logger.info("  LLM Model    : %s", LLM_MODEL)
    logger.info("  LLM Ready    : %s", llm_ready)
    if not llm_ready:
        logger.info("  (using algorithmic fallback — set API key in .env to enable AI)")
    logger.info("  API docs     : http://localhost:8080/docs")
    logger.info("  UI           : http://localhost:8080/")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def _shutdown():
    logger.info("NeoArchAI shutting down.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config import APP_HOST, APP_PORT, DEBUG

    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=DEBUG,
        log_level="info",
        access_log=True,
    )
