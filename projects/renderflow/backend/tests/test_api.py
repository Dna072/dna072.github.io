"""API endpoint tests (submission, listing, filters, retry, health)."""

from __future__ import annotations


def _submit(client, **overrides):
    body = {"job_type": "metadata", "input_uri": "file://sample.mp4"}
    body.update(overrides)
    return client.post("/api/v1/jobs", json=body)


def test_health_and_ready(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["checks"]["database"] == "ok"


def test_request_id_header_roundtrip(client):
    r = client.get("/health", headers={"X-Request-ID": "trace-42"})
    assert r.headers["X-Request-ID"] == "trace-42"


def test_submit_job_returns_queued(client):
    r = _submit(client, priority=5)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "queued"
    assert body["priority"] == 5
    assert body["job_type"] == "metadata"


def test_submit_validation_error(client):
    r = _submit(client, input_uri="")
    assert r.status_code == 422


def test_idempotent_submit_returns_200_second_time(client):
    r1 = _submit(client, idempotency_key="dup-key")
    r2 = _submit(client, idempotency_key="dup-key")
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_get_job_and_404(client):
    job_id = _submit(client).json()["id"]
    assert client.get(f"/api/v1/jobs/{job_id}").status_code == 200
    assert client.get("/api/v1/jobs/does-not-exist").status_code == 404


def test_list_and_filter_jobs(client):
    _submit(client, job_type="metadata")
    _submit(client, job_type="thumbnail")

    r = client.get("/api/v1/jobs")
    assert r.json()["total"] == 2

    r = client.get("/api/v1/jobs", params={"job_type": "thumbnail"})
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["job_type"] == "thumbnail"

    r = client.get("/api/v1/jobs", params={"status": "queued"})
    assert r.json()["total"] == 2


def test_job_stats(client):
    _submit(client)
    _submit(client)
    r = client.get("/api/v1/jobs/stats")
    body = r.json()
    assert body["total"] == 2
    assert body["counts"].get("queued") == 2


def test_cancel_job(client):
    job_id = _submit(client).json()["id"]
    r = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_retry_non_failed_job_conflicts(client):
    job_id = _submit(client).json()["id"]
    # Job is queued (not failed) -> retry should conflict.
    r = client.post(f"/api/v1/jobs/{job_id}/retry")
    assert r.status_code == 409


def test_failed_jobs_list_and_retry_endpoint(client):
    # Submit a job that the worker will force-fail with no retries left.
    r = _submit(client, params={"force_fail": True}, max_retries=0)
    job_id = r.json()["id"]

    # Drive the worker once to process (and fail) the job.
    from app.worker.runner import Worker

    worker = Worker()
    worker.run_once(job_id)

    detail = client.get(f"/api/v1/jobs/{job_id}").json()
    assert detail["status"] == "failed"
    assert detail["error_message"]

    failed = client.get("/api/v1/jobs/failed").json()
    assert failed["total"] == 1

    # Operator retry moves it back to queued.
    r = client.post(f"/api/v1/jobs/{job_id}/retry", params={"reset_retries": True})
    assert r.status_code == 200
    assert r.json()["status"] == "queued"


def test_worker_end_to_end_success(client):
    """A metadata job flows queued -> running -> succeeded via the worker."""
    from app.worker.runner import Worker

    job_id = _submit(client, job_type="metadata").json()["id"]

    worker = Worker()
    worker.run_once(job_id)

    detail = client.get(f"/api/v1/jobs/{job_id}").json()
    assert detail["status"] == "succeeded"
    assert detail["result"] is not None
    assert detail["completed_at"] is not None

    # Worker heartbeat should now be visible.
    workers = client.get("/api/v1/workers").json()
    assert workers["total"] >= 1


def test_worker_transcode_produces_output(client):
    """Transcode job should produce a stored (mock) output artifact."""
    from app.worker.runner import Worker

    job_id = _submit(client, job_type="transcode", params={"height": 480}).json()["id"]
    Worker().run_once(job_id)

    detail = client.get(f"/api/v1/jobs/{job_id}").json()
    assert detail["status"] == "succeeded"
    assert detail["output_uri"]
    assert detail["result"]["height"] == 480
