"""ClipForge FastAPI application entrypoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import __version__
from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

configure_logging(json_logs=settings.is_production, level="DEBUG" if settings.debug else "INFO")
logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])

DESCRIPTION = """
**ClipForge** is an AI video processing & content intelligence platform.

Upload a video and ClipForge asynchronously extracts metadata, generates a
thumbnail and audio track, transcribes speech, and produces an AI summary,
chapters, and tags. Runs fully in **demo mode** (MockAIProvider) with no API key.

Built as a production-style portfolio project.
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # --- exception handlers ---
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "detail": exc.detail}},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
        logger.error("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "detail": "Internal server error"}},
        )

    # --- routes ---
    from app.api.v1 import health as health_module

    app.include_router(health_module.router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # --- static media (local storage; S3/CloudFront in production) ---
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(storage_dir)), name="media")

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    logger.info(
        "app_initialized",
        environment=settings.environment,
        ai_provider="openai" if settings.use_openai else "mock",
    )
    return app


app = create_app()
