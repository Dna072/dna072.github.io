"""StreamPulse FastAPI application entrypoint."""
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.routers import audience, auth, device, geo, overview, timeseries, videos
from app.schemas import HealthResponse, ReadyResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Video analytics API powering the StreamPulse dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(overview.router)
app.include_router(timeseries.router)
app.include_router(videos.router)
app.include_router(audience.router)
app.include_router(geo.router)
app.include_router(device.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Liveness probe: process is up. No external dependencies checked."""
    return HealthResponse(status="ok")


@app.get("/ready", response_model=ReadyResponse, tags=["system"])
def ready(response: Response) -> ReadyResponse:
    """Readiness probe: confirms the database connection is usable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return ReadyResponse(status="ok", database="ok")
    except Exception:  # noqa: BLE001
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="unavailable", database="unreachable")
