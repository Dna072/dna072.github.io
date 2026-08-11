"""Video upload / CRUD / search API tests."""

from __future__ import annotations

import io


def _workspace_id(auth_client) -> str:
    resp = auth_client.get("/api/v1/workspaces")
    assert resp.status_code == 200, resp.text
    workspaces = resp.json()
    assert workspaces, "registration should create a default workspace"
    return workspaces[0]["id"]


def _upload(auth_client, workspace_id, *, filename="clip.mp4", content_type="video/mp4",
            content=b"fake-video-bytes", title="My Clip"):
    return auth_client.post(
        "/api/v1/videos/upload",
        data={"workspace_id": workspace_id, "title": title},
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


def test_upload_creates_video_and_job(auth_client, _stub_queue):
    ws = _workspace_id(auth_client)
    resp = _upload(auth_client, ws)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["video"]["title"] == "My Clip"
    assert body["video"]["status"] == "queued"
    assert body["job_id"]
    # The upload should have enqueued exactly one job.
    assert body["job_id"] in _stub_queue.enqueued


def test_upload_rejects_bad_extension(auth_client):
    ws = _workspace_id(auth_client)
    resp = _upload(auth_client, ws, filename="notes.txt", content_type="text/plain")
    assert resp.status_code == 422


def test_upload_rejects_bad_mime(auth_client):
    ws = _workspace_id(auth_client)
    resp = _upload(auth_client, ws, filename="clip.mp4", content_type="text/plain")
    assert resp.status_code == 422


def test_upload_requires_auth(client):
    resp = client.post(
        "/api/v1/videos/upload",
        data={"workspace_id": "nope"},
        files={"file": ("c.mp4", io.BytesIO(b"x"), "video/mp4")},
    )
    assert resp.status_code == 401


def test_list_and_get_video(auth_client):
    ws = _workspace_id(auth_client)
    video_id = _upload(auth_client, ws, title="Listed").json()["video"]["id"]

    listing = auth_client.get("/api/v1/videos")
    assert listing.status_code == 200
    page = listing.json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == video_id

    detail = auth_client.get(f"/api/v1/videos/{video_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Listed"


def test_search_filters_by_query(auth_client):
    ws = _workspace_id(auth_client)
    _upload(auth_client, ws, title="Alpha Keynote")
    _upload(auth_client, ws, title="Beta Tutorial")

    resp = auth_client.get("/api/v1/search", params={"q": "keynote"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Alpha Keynote"


def test_update_video_metadata(auth_client):
    ws = _workspace_id(auth_client)
    video_id = _upload(auth_client, ws).json()["video"]["id"]

    resp = auth_client.patch(
        f"/api/v1/videos/{video_id}",
        json={"title": "Renamed", "tags": ["demo", "test"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Renamed"
    assert body["tags"] == ["demo", "test"]


def test_delete_video(auth_client):
    ws = _workspace_id(auth_client)
    video_id = _upload(auth_client, ws).json()["video"]["id"]

    assert auth_client.delete(f"/api/v1/videos/{video_id}").status_code == 200
    assert auth_client.get(f"/api/v1/videos/{video_id}").status_code == 404


def test_cannot_access_other_users_video(auth_client, client):
    ws = _workspace_id(auth_client)
    video_id = _upload(auth_client, ws).json()["video"]["id"]

    # Second, separate user.
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "password123",
            "full_name": "Other",
        },
    ).json()["tokens"]["access_token"]
    resp = client.get(
        f"/api/v1/videos/{video_id}",
        headers={"Authorization": f"Bearer {other}"},
    )
    assert resp.status_code == 404
