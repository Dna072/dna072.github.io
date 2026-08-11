"""FastAPI application entrypoint.

Wires together configuration, structured logging, request-ID correlation, the
routers, and a background reaper that recovers jobs abandoned by dead workers.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .config import get_settings
from .database import SessionLocal, init_db
from .logging_config import configure_logging, request_id_ctx
from .reaper import ReaperThread
from .routers import health, jobs, workers

logger = logging.getLogger("renderflow.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, settings.service_name)
    init_db()
    logger.info("starting RenderFlow API", extra={"environment": settings.environment})

    reaper = ReaperThread(SessionLocal, interval_seconds=15.0)
    reaper.start()
    app.state.reaper = reaper
    try:
        yield
    finally:
        reaper.stop()
        logger.info("RenderFlow API shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="RenderFlow",
        description="Distributed media processing platform — job orchestration API.",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        """Attach a request id, log the request, and time it."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001
            logger.exception(
                "unhandled error",
                extra={"path": request.url.path, "method": request.method},
            )
            response = JSONResponse(
                status_code=500, content={"detail": "internal server error"}
            )
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        # Skip access logs for probes to keep signal-to-noise high.
        if request.url.path not in {"/health", "/ready"}:
            logger.info(
                "request handled",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
        request_id_ctx.reset(token)
        return response

    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(workers.router)

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "service": settings.service_name,
            "version": __version__,
            "docs": "/docs",
        }

    return app


app = create_app()
