"""Health and readiness probe tests."""

from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_reports_database(client):
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["checks"]["database"] == "ok"
    assert body["status"] == "ready"


def test_request_id_header_present(client):
    resp = client.get("/api/v1/health")
    assert resp.headers.get("X-Request-ID")
