"""FastAPI application factory and entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router, root_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.utils.files import ensure_storage_dir

logger = get_logger("clipforge.app")

DESCRIPTION = """
**ClipForge** is an AI video processing & content intelligence platform.

Upload videos, run them through an asynchronous processing pipeline
(probe → thumbnail → audio → transcript → AI summary/chapters/tags), and
explore the results through a searchable library and dashboard.
""".strip()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    configure_logging(settings.log_level, settings.log_json)
    ensure_storage_dir()
    logger.info(
        "app_startup",
        extra={
            "environment": settings.environment,
            "ai_provider": settings.resolved_ai_provider(),
        },
    )
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):  # noqa: ARG001
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    app.include_router(root_router)
    app.include_router(api_router)

    @app.get("/", tags=["meta"])
    async def root():
        return {
            "service": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
