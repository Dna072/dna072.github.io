from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal, engine
from app.middleware.request_id import RequestIDMiddleware

configure_logging()
logger = get_logger("mediavault.app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("startup", env=settings.ENV)
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "MediaVault API — video asset management for creative teams. "
        "Workspaces, RBAC, folders, tags, full-text search, and signed share links."
    ),
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = jsonable_encoder(exc.errors(), exclude={"ctx"})
    logger.warning("validation_error", path=request.url.path, errors=errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe: is the process up? Does not touch external systems."""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready() -> JSONResponse:
    """Readiness probe: can we actually serve traffic (i.e. reach the DB)?"""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status": "ready", "database": "up"})
    except Exception as exc:  # pragma: no cover - exercised via integration/infra checks
        logger.error("readiness_check_failed", error=str(exc))
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "database": "down"}
        )


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


_ = engine  # ensures the module-level engine is created eagerly at import time
