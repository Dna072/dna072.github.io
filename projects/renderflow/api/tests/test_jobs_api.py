def test_root_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health/live").json() == {"status": "ok"}

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"] == {"database": True, "redis": True}


def test_create_and_get_job(client):
    resp = client.post(
        "/api/v1/jobs",
        json={"job_type": "transcode", "input_uri": "s3://bucket/in.mp4", "priority": 7},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "queued"
    assert body["priority"] == 7

    job_id = body["id"]
    fetched = client.get(f"/api/v1/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == job_id


def test_get_missing_job_404(client):
    resp = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_create_job_validates_job_type(client):
    resp = client.post("/api/v1/jobs", json={"job_type": "not_a_type", "input_uri": "x"})
    assert resp.status_code == 422


def test_idempotent_create_returns_same_job_200(client):
    payload = {
        "job_type": "audio_extract",
        "input_uri": "s3://bucket/in.mov",
        "idempotency_key": "abc-123",
    }
    first = client.post("/api/v1/jobs", json=payload)
    second = client.post("/api/v1/jobs", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_list_jobs_filters_by_status_and_type(client):
    client.post("/api/v1/jobs", json={"job_type": "transcode", "input_uri": "a"})
    client.post("/api/v1/jobs", json={"job_type": "thumbnail", "input_uri": "b"})

    all_jobs = client.get("/api/v1/jobs").json()
    assert all_jobs["total"] == 2

    only_thumbnails = client.get("/api/v1/jobs", params={"job_type": "thumbnail"}).json()
    assert only_thumbnails["total"] == 1
    assert only_thumbnails["items"][0]["job_type"] == "thumbnail"

    only_queued = client.get("/api/v1/jobs", params={"status": "queued"}).json()
    assert only_queued["total"] == 2


def test_retry_endpoint_requires_failed_status(client):
    created = client.post("/api/v1/jobs", json={"job_type": "metadata", "input_uri": "a"}).json()

    # Fresh job is "queued", not "failed" -> retry should be rejected.
    retry_resp = client.post(f"/api/v1/jobs/{created['id']}/retry")
    assert retry_resp.status_code == 409


def test_cancel_then_stats(client):
    created = client.post("/api/v1/jobs", json={"job_type": "metadata", "input_uri": "a"}).json()
    cancel_resp = client.post(f"/api/v1/jobs/{created['id']}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    stats = client.get("/api/v1/jobs/stats").json()
    assert stats["by_status"]["cancelled"] == 1
    assert stats["total"] == 1


def test_workers_list_empty_by_default(client):
    resp = client.get("/api/v1/workers")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}
