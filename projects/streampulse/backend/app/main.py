"""StreamPulse API application factory."""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.routes import analytics, auth, health
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, request_id_ctx

configure_logging(settings.log_level, settings.log_json)
log = get_logger("streampulse")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request id, time the request, and emit a structured access log."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise
        finally:
            request_id_ctx.reset(token)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = rid
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("startup", environment=settings.environment, version=__version__)
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=__version__,
        description="Video analytics & performance API — charts are served from real aggregations.",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Probes live at the root; business endpoints under the versioned prefix.
    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(analytics.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
