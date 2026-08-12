"""Structured logging configuration with request-id propagation."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Populated by the request-id middleware for each inbound request.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects for log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id

        # Merge any structured extras attached via logger.info(..., extra={...}).
        for key, value in record.__dict__.get("extra_fields", {}).items():
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    """Human-friendly formatter used for local development."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = request_id_ctx.get()
        prefix = f"[{request_id}] " if request_id else ""
        base = f"{self.formatTime(record)} {record.levelname:<7} {record.name}: {prefix}{record.getMessage()}"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


class StructuredLogger(logging.LoggerAdapter):
    """Logger adapter that forwards keyword fields into structured output."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        extra = kwargs.pop("extra", {}) or {}
        fields = dict(kwargs.pop("fields", {})) if "fields" in kwargs else {}
        extra["extra_fields"] = fields
        kwargs["extra"] = extra
        return msg, kwargs


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Install a root logging handler with the requested formatter."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_output else TextFormatter())
    root.addHandler(handler)

    # Tame noisy third-party loggers.
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").propagate = True


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name), {})
