import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from renderflow_common.config import Settings, get_settings
from renderflow_common.db import make_engine, make_session_factory
from renderflow_common.models import Base
from renderflow_common.queue import get_redis

from .routers import health, jobs, workers
from .scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("renderflow.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app.

    Accepting `settings` (rather than always reaching for the process-wide
    singleton) is what lets the test suite point the whole app at an
    in-memory SQLite DB and a fake Redis without any monkeypatching.
    """
    settings = settings or get_settings()
    engine = make_engine(settings)
    session_factory = make_session_factory(engine)
    redis_client = get_redis(settings.redis_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Convenience for local/dev/CI; production applies migrations
        # explicitly via `alembic upgrade head` (see Dockerfile CMD).
        Base.metadata.create_all(bind=engine)

        task = asyncio.create_task(scheduler_loop(session_factory, redis_client, settings))
        logger.info("RenderFlow API started")
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(
        title="RenderFlow API",
        description="Distributed media processing: job submission, tracking, retries and worker visibility.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.redis_client = redis_client

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(workers.router)

    @app.get("/")
    def root():
        return {"service": "renderflow-api", "docs": "/docs"}

    return app


app = create_app()
