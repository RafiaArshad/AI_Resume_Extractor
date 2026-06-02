# app/main.py
"""
AI Resume Parser — FastAPI Application Entry Point

✔ Hybrid extraction (Gemini + Regex)
✔ CORS configured properly
✔ Structured error responses
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv  #type: ignore
from fastapi import FastAPI, HTTPException, Request  # type: ignore
from fastapi.exceptions import RequestValidationError     #type: ignore
from fastapi.middleware.cors import CORSMiddleware   #type: ignore
from fastapi.responses import JSONResponse    #type: ignore

from app.api.routes import upload
from app.services.database import close_db, connect_db, get_db
from app.services.ollama_extractor import get_best_model, is_ollama_available


load_dotenv()

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ai-resume-parser")

# Runtime state
_RUNTIME: dict = {
    "ollama_active": False,
    "ollama_model": None,
}

# ─────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()

    logger.info("=" * 60)
    logger.info("  AI Resume Parser — Production Engine v1.2")
    logger.info("=" * 60)

    ollama_active = is_ollama_available()
    ollama_model = get_best_model() if ollama_active else None

    _RUNTIME["ollama_active"] = ollama_active
    _RUNTIME["ollama_model"] = ollama_model

    if ollama_active:
        logger.info("Extraction Mode : HYBRID (Gemini + regex)")
        logger.info("Model    : %s", ollama_model)
    else:
        logger.info("Extraction Mode : REGEX ONLY")
        logger.info("Gemini         : OFFLINE")

    logger.info("=" * 60)

    yield

    await close_db()
    logger.info("Shutdown complete")


# ─────────────────────────────────────────────────────────────
# App initialization
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Resume Parser",
    version="1.2.0",
    description="Hybrid resume parser using Gemini + Regex fallback",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────────────────────
# CORS (FIXED — IMPORTANT)
# ─────────────────────────────────────────────────────────────

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173, " \
    "http://127.0.0.1:5173, " \
    "http://localhost:3000, " \
    "http://localhost:5713",
)

ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

app.include_router(upload.router, prefix="/api/resume")

# ─────────────────────────────────────────────────────────────
# Health endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    db_status = "connected"
    try:
        await get_db().command("ping")
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "ollama": {
            "active": _RUNTIME["ollama_active"],
            "model": _RUNTIME["ollama_model"],
        },
        "version": "1.2.0",
    }


@app.get("/", tags=["System"])
async def root():
    mode = (
        f"hybrid (ollama:{_RUNTIME['ollama_model']})"
        if _RUNTIME["ollama_active"]
        else "regex-only"
    )

    return {
        "service": "AI Resume Parser",
        "version": "1.2.0",
        "engine": mode,
        "docs": "/docs",
    }

# ─────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Request validation failed",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s", request.method, request.url, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
    )
