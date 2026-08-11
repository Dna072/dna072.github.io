"""Structured logging configuration.

Emits JSON log lines (production) or human-readable lines (local debug) and
enriches every record with the current request ID when one is available.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Holds the request id for the currently handled request (set by middleware).
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Attach the current request id to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """Serialize log records as single-line JSON documents."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include any structured extras passed via ``extra={...}``.
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload.setdefault(key, value)
        return json.dumps(payload, default=str)


_RESERVED_ATTRS = set(
    logging.makeLogRecord({}).__dict__.keys()
) | {"request_id", "message", "asctime"}


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure root logging handlers once at startup."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Remove default handlers to avoid duplicate log lines.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"
            )
        )
    root.addHandler(handler)

    # Tone down noisy third-party loggers.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
