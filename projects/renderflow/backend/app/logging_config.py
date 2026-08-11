"""Structured (JSON) logging with per-request correlation IDs.

Every log line carries a ``request_id`` when one is available, which makes it
trivial to trace a single API call or job across the API and worker logs in a
production log aggregator (CloudWatch, Loki, Datadog, ...).
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

# Correlation identifiers propagated via contextvars so they are available to
# any log record emitted while handling a request or processing a job.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)
worker_id_ctx: ContextVar[str | None] = ContextVar("worker_id", default=None)

_RESERVED = set(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=UTC
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id
        job_id = job_id_ctx.get()
        if job_id:
            payload["job_id"] = job_id
        worker_id = worker_id_ctx.get()
        if worker_id:
            payload["worker_id"] = worker_id

        # Include any structured "extra" fields attached to the record.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", service_name: str = "renderflow") -> None:
    """Configure the root logger to emit JSON to stdout (12-factor style)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Tame noisy third-party loggers.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(service_name).info(
        "logging configured", extra={"service": service_name, "level": level}
    )
