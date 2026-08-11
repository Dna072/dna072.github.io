"""Tests for the job state machine."""

from __future__ import annotations

import pytest

from app.state_machine import (
    ACTIVE_STATES,
    TERMINAL_STATES,
    InvalidTransition,
    JobStatus,
    assert_transition,
    can_transition,
    is_retryable,
    is_terminal,
)


def test_happy_path_transitions():
    assert can_transition(JobStatus.PENDING, JobStatus.QUEUED)
    assert can_transition(JobStatus.QUEUED, JobStatus.RUNNING)
    assert can_transition(JobStatus.RUNNING, JobStatus.SUCCEEDED)


def test_retry_cycle_transitions():
    assert can_transition(JobStatus.RUNNING, JobStatus.RETRYING)
    assert can_transition(JobStatus.RETRYING, JobStatus.QUEUED)


def test_terminal_states_are_terminal():
    assert TERMINAL_STATES == {
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }
    for state in TERMINAL_STATES:
        assert is_terminal(state)
    for state in ACTIVE_STATES:
        assert not is_terminal(state)


def test_succeeded_is_fully_terminal():
    for target in JobStatus:
        assert not can_transition(JobStatus.SUCCEEDED, target)


def test_failed_and_cancelled_allow_requeue():
    assert can_transition(JobStatus.FAILED, JobStatus.QUEUED)
    assert can_transition(JobStatus.CANCELLED, JobStatus.QUEUED)
    assert is_retryable(JobStatus.FAILED)
    assert is_retryable(JobStatus.CANCELLED)
    assert not is_retryable(JobStatus.SUCCEEDED)


def test_invalid_transitions_raise():
    with pytest.raises(InvalidTransition):
        assert_transition(JobStatus.SUCCEEDED, JobStatus.RUNNING)
    with pytest.raises(InvalidTransition):
        assert_transition(JobStatus.PENDING, JobStatus.SUCCEEDED)
    with pytest.raises(InvalidTransition):
        assert_transition(JobStatus.QUEUED, JobStatus.SUCCEEDED)


def test_cancel_allowed_from_all_active_states():
    for state in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING):
        assert can_transition(state, JobStatus.CANCELLED)
