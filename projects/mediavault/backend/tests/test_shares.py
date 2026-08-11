from datetime import UTC, datetime, timedelta

import pytest

from app.models.share import Share


@pytest.fixture
def ws(client, register_user, auth_headers, make_workspace):
    tokens = register_user(client, email="shares-owner@example.com")
    headers = auth_headers(tokens)
    workspace = make_workspace(client, headers)
    return {"id": workspace["id"], "headers": headers}


@pytest.fixture
def asset(client, ws):
    return client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("shareable.mp4", b"shareable-bytes", "video/mp4")},
        headers=ws["headers"],
    ).json()


def test_create_view_only_share(client, ws, asset):
    response = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/shares",
        json={"permission": "VIEW"},
        headers=ws["headers"],
    )
    assert response.status_code == 201
    share = response.json()
    assert share["is_active"] is True

    public_response = client.get(f"/api/v1/shares/public/{share['token']}")
    assert public_response.status_code == 200
    assert public_response.json()["download_url"] is None


def test_download_share_allows_file_download(client, ws, asset):
    share = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/shares",
        json={"permission": "DOWNLOAD"},
        headers=ws["headers"],
    ).json()

    public_response = client.get(f"/api/v1/shares/public/{share['token']}")
    download_url = public_response.json()["download_url"]
    assert download_url is not None

    download_response = client.get(download_url)
    assert download_response.status_code == 200
    assert download_response.content == b"shareable-bytes"


def test_view_only_share_rejects_download_attempt(client, ws, asset):
    share = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/shares",
        json={"permission": "VIEW"},
        headers=ws["headers"],
    ).json()
    response = client.get(f"/api/v1/shares/public/{share['token']}/download")
    assert response.status_code == 403


def test_revoked_share_is_gone(client, ws, asset):
    share = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/shares",
        json={"permission": "VIEW"},
        headers=ws["headers"],
    ).json()
    revoke_response = client.delete(
        f"/api/v1/workspaces/{ws['id']}/shares/{share['id']}", headers=ws["headers"]
    )
    assert revoke_response.status_code == 200

    public_response = client.get(f"/api/v1/shares/public/{share['token']}")
    assert public_response.status_code == 410


def test_expired_share_is_gone(client, ws, asset, db):
    share = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/shares",
        json={"permission": "VIEW", "expires_in_hours": 1},
        headers=ws["headers"],
    ).json()

    # Simulate time passing by backdating the share's expiry directly.
    record = db.query(Share).filter(Share.id == share["id"]).one()
    record.expires_at = datetime.now(UTC) - timedelta(hours=1)
    db.add(record)
    db.commit()

    public_response = client.get(f"/api/v1/shares/public/{share['token']}")
    assert public_response.status_code == 410


def test_unknown_share_token_404(client):
    response = client.get("/api/v1/shares/public/not-a-real-token")
    assert response.status_code == 404


def test_viewer_cannot_create_share(client, ws, asset, register_user, auth_headers):
    viewer_tokens = register_user(client, email="shares-viewer@example.com")
    client.post(
        f"/api/v1/workspaces/{ws['id']}/members",
        json={"email": "shares-viewer@example.com", "role": "VIEWER"},
        headers=ws["headers"],
    )
    response = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/shares",
        json={"permission": "VIEW"},
        headers=auth_headers(viewer_tokens),
    )
    assert response.status_code == 403
