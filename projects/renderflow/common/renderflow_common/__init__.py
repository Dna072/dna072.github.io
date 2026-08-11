"""Shared code used by both the RenderFlow API and worker processes.

Kept intentionally small: ORM models, Pydantic schemas, settings and the
Redis queue helpers. Both services install this package in editable mode
(see their Dockerfiles) so the job state machine lives in exactly one place.
"""

__version__ = "0.1.0"
