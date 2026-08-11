"""Job lifecycle state machine.

Centralising valid transitions here keeps the API, worker, and reaper honest:
every status change is validated against this map, so an invalid transition
(e.g. resurrecting a ``SUCCEEDED`` job) raises instead of silently corrupting
state.
"""

from __future__ import annotations

import enum


class JobStatus(str, enum.Enum):
    """All states a job may occupy."""

    PENDING = "pending"        # created, not yet placed on the queue
    QUEUED = "queued"          # on the queue, waiting for a worker
    RUNNING = "running"        # claimed by a worker, being processed
    RETRYING = "retrying"      # failed, waiting for backoff before re-queue
    SUCCEEDED = "succeeded"    # terminal: completed successfully
    FAILED = "failed"          # terminal: exhausted retries / permanent error
    CANCELLED = "cancelled"    # terminal: cancelled by an operator


class JobType(str, enum.Enum):
    """Supported media processing job types."""

    TRANSCODE = "transcode"
    THUMBNAIL = "thumbnail"
    AUDIO_EXTRACT = "audio_extract"
    METADATA = "metadata"


TERMINAL_STATES: frozenset[JobStatus] = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
)

# Active (non-terminal) states — used by the API to decide what can be retried
# or cancelled and by the reaper to find stuck work.
ACTIVE_STATES: frozenset[JobStatus] = frozenset(
    {JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.RETRYING}
)

# Allowed transitions. Any (from -> to) not present here is rejected.
_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.PENDING: frozenset({JobStatus.QUEUED, JobStatus.CANCELLED}),
    JobStatus.QUEUED: frozenset(
        {JobStatus.RUNNING, JobStatus.CANCELLED}
    ),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.RETRYING,
            # A stuck/lost job can be requeued directly by the reaper.
            JobStatus.QUEUED,
            JobStatus.CANCELLED,
        }
    ),
    JobStatus.RETRYING: frozenset({JobStatus.QUEUED, JobStatus.CANCELLED}),
    # Terminal states permit re-queue only via an explicit operator retry
    # (FAILED/CANCELLED -> QUEUED). SUCCEEDED is fully terminal.
    JobStatus.FAILED: frozenset({JobStatus.QUEUED}),
    JobStatus.CANCELLED: frozenset({JobStatus.QUEUED}),
    JobStatus.SUCCEEDED: frozenset(),
}


class InvalidTransition(Exception):
    """Raised when an illegal status transition is attempted."""

    def __init__(self, current: JobStatus, target: JobStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid job transition: {current.value} -> {target.value}"
        )


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    """Return True if ``current -> target`` is a permitted transition."""
    return target in _TRANSITIONS.get(current, frozenset())


def assert_transition(current: JobStatus, target: JobStatus) -> None:
    """Raise :class:`InvalidTransition` if the transition is not permitted."""
    if not can_transition(current, target):
        raise InvalidTransition(current, target)


def is_terminal(status: JobStatus) -> bool:
    return status in TERMINAL_STATES


def is_retryable(status: JobStatus) -> bool:
    """Whether an operator may re-queue a job in this state."""
    return status in {JobStatus.FAILED, JobStatus.CANCELLED}
