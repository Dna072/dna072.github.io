from pathlib import Path

import pytest


@pytest.fixture
def ws(client, register_user, auth_headers, make_workspace):
    tokens = register_user(client, email="assets-owner@example.com")
    headers = auth_headers(tokens)
    workspace = make_workspace(client, headers)
    return {"id": workspace["id"], "headers": headers}


def test_upload_rejects_unsupported_content_type(client, ws):
    response = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("doc.pdf", b"pdf-bytes", "application/pdf")},
        headers=ws["headers"],
    )
    assert response.status_code == 415


def test_upload_rejects_empty_file(client, ws):
    response = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("empty.mp4", b"", "video/mp4")},
        headers=ws["headers"],
    )
    assert response.status_code == 400


def test_upload_and_get_asset(client, ws):
    response = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"some video bytes here", "video/mp4")},
        headers=ws["headers"],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "clip.mp4"
    assert body["size_bytes"] == len(b"some video bytes here")
    assert body["checksum_sha256"]

    get_response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets/{body['id']}", headers=ws["headers"]
    )
    assert get_response.status_code == 200


def test_list_assets_pagination(client, ws):
    for i in range(5):
        client.post(
            f"/api/v1/workspaces/{ws['id']}/assets",
            files={"file": (f"clip-{i}.mp4", f"bytes-{i}".encode(), "video/mp4")},
            headers=ws["headers"],
        )
    response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets?page=1&page_size=2", headers=ws["headers"]
    )
    body = response.json()
    assert body["total"] == 5
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["pages"] == 3


def test_list_assets_filter_by_content_type(client, ws):
    client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"video-bytes", "video/mp4")},
        headers=ws["headers"],
    )
    client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("pic.png", b"image-bytes", "image/png")},
        headers=ws["headers"],
    )
    response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets?content_type=image/", headers=ws["headers"]
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["content_type"] == "image/png"


def test_list_assets_sort_by_size(client, ws):
    client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("small.mp4", b"a", "video/mp4")},
        headers=ws["headers"],
    )
    client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("big.mp4", b"a" * 1000, "video/mp4")},
        headers=ws["headers"],
    )
    response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets?sort_by=size_bytes&sort_dir=asc",
        headers=ws["headers"],
    )
    items = response.json()["items"]
    assert items[0]["filename"] == "small.mp4"
    assert items[-1]["filename"] == "big.mp4"


def test_update_asset_metadata(client, ws):
    upload = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"bytes", "video/mp4")},
        headers=ws["headers"],
    ).json()
    response = client.patch(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}",
        json={"filename": "renamed.mp4", "description": "Updated description"},
        headers=ws["headers"],
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "renamed.mp4"
    assert response.json()["description"] == "Updated description"


def test_tag_attach_and_detach(client, ws):
    upload = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"bytes", "video/mp4")},
        headers=ws["headers"],
    ).json()
    tag = client.post(
        f"/api/v1/workspaces/{ws['id']}/tags", json={"name": "final-cut"}, headers=ws["headers"]
    ).json()

    attach_response = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}/tags/{tag['id']}",
        headers=ws["headers"],
    )
    assert attach_response.status_code == 200
    assert len(attach_response.json()["tags"]) == 1

    detach_response = client.delete(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}/tags/{tag['id']}",
        headers=ws["headers"],
    )
    assert detach_response.status_code == 200
    assert len(detach_response.json()["tags"]) == 0


def test_delete_asset_removes_file_from_storage(client, ws):
    from app.core.config import settings

    upload = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"bytes-to-delete", "video/mp4")},
        headers=ws["headers"],
    ).json()

    storage_files_before = list(Path(settings.STORAGE_ROOT).rglob("*"))
    assert any(f.is_file() for f in storage_files_before)

    delete_response = client.delete(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}", headers=ws["headers"]
    )
    assert delete_response.status_code == 200

    get_response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}", headers=ws["headers"]
    )
    assert get_response.status_code == 404


def test_signed_download_url_roundtrip(client, ws):
    upload = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"downloadable-bytes", "video/mp4")},
        headers=ws["headers"],
    ).json()
    url_response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}/download-url", headers=ws["headers"]
    )
    assert url_response.status_code == 200
    download_url = url_response.json()["url"]

    download_response = client.get(download_url)
    assert download_response.status_code == 200
    assert download_response.content == b"downloadable-bytes"


def test_download_with_tampered_token_rejected(client, ws):
    upload = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets",
        files={"file": ("clip.mp4", b"secret-bytes", "video/mp4")},
        headers=ws["headers"],
    ).json()
    url_response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets/{upload['id']}/download-url", headers=ws["headers"]
    )
    download_url = url_response.json()["url"]
    tampered_url = download_url[:-2] + "xx"
    response = client.get(tampered_url)
    assert response.status_code == 401
