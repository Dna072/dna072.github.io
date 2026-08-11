from __future__ import annotations

import io


def _create_project(auth_client) -> str:
    workspaces = auth_client.get("/api/v1/workspaces").json()
    ws_id = workspaces[0]["id"]
    proj = auth_client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Campaign", "description": "Test project"},
    )
    assert proj.status_code == 201, proj.text
    return proj.json()["id"]


def _upload(auth_client, project_id: str, name="clip.mp4"):
    return auth_client.post(
        "/api/v1/videos",
        data={"project_id": project_id, "title": "My Clip"},
        files={"file": (name, io.BytesIO(b"fake-mp4-bytes" * 100), "video/mp4")},
    )


def test_upload_queues_video(auth_client, memory_queue):
    project_id = _create_project(auth_client)
    resp = _upload(auth_client, project_id)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    assert body["title"] == "My Clip"
    # A job message was enqueued.
    msg = memory_queue.dequeue()
    assert msg is not None
    assert msg["video_id"] == body["id"]


def test_upload_rejects_bad_extension(auth_client):
    project_id = _create_project(auth_client)
    resp = auth_client.post(
        "/api/v1/videos",
        data={"project_id": project_id},
        files={"file": ("bad.exe", io.BytesIO(b"x" * 50), "video/mp4")},
    )
    assert resp.status_code == 422


def test_video_status_endpoint(auth_client):
    project_id = _create_project(auth_client)
    video_id = _upload(auth_client, project_id).json()["id"]
    resp = auth_client.get(f"/api/v1/videos/{video_id}/status")
    assert resp.status_code == 200
    assert resp.json()["video_id"] == video_id
    assert len(resp.json()["steps"]) == 5


def test_search_and_filter(auth_client):
    project_id = _create_project(auth_client)
    _upload(auth_client, project_id, name="alpha.mp4")
    _upload(auth_client, project_id, name="beta.mp4")
    resp = auth_client.get("/api/v1/videos", params={"limit": 10})
    assert resp.status_code == 200
    page = resp.json()
    assert page["total"] == 2
    assert len(page["items"]) == 2

    # Filter by status
    filtered = auth_client.get("/api/v1/videos", params={"status": "queued"})
    assert filtered.json()["total"] == 2


def test_cannot_access_other_users_video(client, auth_client):
    project_id = _create_project(auth_client)
    video_id = _upload(auth_client, project_id).json()["id"]

    # Second user
    client.post(
        "/api/v1/auth/register",
        json={"email": "intruder@b.com", "full_name": "I", "password": "password123"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "intruder@b.com", "password": "password123"}
    ).json()
    resp = client.get(
        f"/api/v1/videos/{video_id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 404


def test_delete_video(auth_client):
    project_id = _create_project(auth_client)
    video_id = _upload(auth_client, project_id).json()["id"]
    assert auth_client.delete(f"/api/v1/videos/{video_id}").status_code == 204
    assert auth_client.get(f"/api/v1/videos/{video_id}").status_code == 404
