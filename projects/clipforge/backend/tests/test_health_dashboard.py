from __future__ import annotations

import io


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert "database" in body
    assert body["database"] is True


def test_dashboard_stats_empty(auth_client):
    resp = auth_client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_videos"] == 0
    assert body["total_projects"] == 0


def test_dashboard_stats_after_upload(auth_client):
    workspaces = auth_client.get("/api/v1/workspaces").json()
    ws_id = workspaces[0]["id"]
    project_id = auth_client.post(
        f"/api/v1/workspaces/{ws_id}/projects", json={"name": "P"}
    ).json()["id"]
    auth_client.post(
        "/api/v1/videos",
        data={"project_id": project_id},
        files={"file": ("clip.mp4", io.BytesIO(b"data" * 100), "video/mp4")},
    )
    resp = auth_client.get("/api/v1/dashboard/stats")
    body = resp.json()
    assert body["total_videos"] == 1
    assert body["total_projects"] == 1
    assert len(body["recent_videos"]) == 1


def test_openapi_available(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"]
