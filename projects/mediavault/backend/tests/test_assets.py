"""Asset upload, validation, signed URL and share-flow tests."""

from __future__ import annotations

import io

PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da63f8cff0bf1f0005ff02fedca4b9740000000049454e44ae426082"
)


def _upload(client, ws_id, headers, name="clip.png", content_type="image/png", folder_id=None):
    data = {"name": name}
    if folder_id:
        data["folder_id"] = folder_id
    return client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=headers,
        files={"file": (name, io.BytesIO(PNG_1x1), content_type)},
        data=data,
    )


def test_upload_and_get_asset(client, admin_headers, workspace):
    ws_id = workspace["id"]
    resp = _upload(client, ws_id, admin_headers, name="Launch Teaser.png")
    assert resp.status_code == 201, resp.text
    asset = resp.json()
    assert asset["kind"] == "IMAGE"
    assert asset["size_bytes"] > 0
    assert asset["checksum_sha256"]

    got = client.get(f"/api/v1/workspaces/{ws_id}/assets/{asset['id']}", headers=admin_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Launch Teaser.png"


def test_upload_rejects_unsupported_type(client, admin_headers, workspace):
    ws_id = workspace["id"]
    resp = client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=admin_headers,
        files={"file": ("evil.exe", io.BytesIO(b"MZ..."), "application/x-msdownload")},
    )
    assert resp.status_code == 415


def test_upload_rejects_content_type_mismatch(client, admin_headers, workspace):
    ws_id = workspace["id"]
    resp = client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=admin_headers,
        files={"file": ("fake.png", io.BytesIO(b"not-a-real-png"), "image/png")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "content_type_mismatch"


def test_upload_accepts_mislabeled_but_valid_png(client, admin_headers, workspace):
    """Browsers sometimes send image/jpeg for a PNG — trust magic bytes."""
    ws_id = workspace["id"]
    resp = client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=admin_headers,
        files={"file": ("shot.jpg", io.BytesIO(PNG_1x1), "image/jpeg")},
        data={"name": "Mislabeled"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["content_type"] == "image/png"
    assert resp.json()["kind"] == "IMAGE"


def test_upload_accepts_jpg_alias_and_octet_stream(client, admin_headers, workspace):
    ws_id = workspace["id"]
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 64
    alias = client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=admin_headers,
        files={"file": ("photo.jpg", io.BytesIO(jpeg), "image/jpg")},
    )
    assert alias.status_code == 201, alias.text
    assert alias.json()["content_type"] == "image/jpeg"

    generic = client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=admin_headers,
        files={"file": ("photo2.jpg", io.BytesIO(jpeg), "application/octet-stream")},
    )
    assert generic.status_code == 201, generic.text
    assert generic.json()["content_type"] == "image/jpeg"


def test_signed_url_download_flow(client, admin_headers, workspace):
    ws_id = workspace["id"]
    asset = _upload(client, ws_id, admin_headers).json()

    signed = client.get(
        f"/api/v1/workspaces/{ws_id}/assets/{asset['id']}/signed-url", headers=admin_headers
    )
    assert signed.status_code == 200
    url = signed.json()["url"]

    # The signed URL requires no auth header but must validate.
    download = client.get(url)
    assert download.status_code == 200
    assert download.content == PNG_1x1


def test_signed_url_tamper_rejected(client, admin_headers, workspace):
    ws_id = workspace["id"]
    asset = _upload(client, ws_id, admin_headers).json()
    signed = client.get(
        f"/api/v1/workspaces/{ws_id}/assets/{asset['id']}/signed-url", headers=admin_headers
    ).json()
    tampered = signed["url"].replace("signature=", "signature=deadbeef")
    assert client.get(tampered).status_code == 403


def test_public_share_flow(client, admin_headers, workspace):
    ws_id = workspace["id"]
    asset = _upload(client, ws_id, admin_headers).json()

    share = client.post(
        f"/api/v1/workspaces/{ws_id}/assets/{asset['id']}/shares",
        json={"max_downloads": 2, "allow_download": True},
        headers=admin_headers,
    )
    assert share.status_code == 201
    token = share.json()["token"]

    view = client.get(f"/api/v1/shares/{token}")
    assert view.status_code == 200
    assert view.json()["name"] == asset["name"]

    dl = client.get(f"/api/v1/shares/{token}/download")
    assert dl.status_code == 200
    assert dl.content == PNG_1x1


def test_share_download_limit_enforced(client, admin_headers, workspace):
    ws_id = workspace["id"]
    asset = _upload(client, ws_id, admin_headers).json()
    token = client.post(
        f"/api/v1/workspaces/{ws_id}/assets/{asset['id']}/shares",
        json={"max_downloads": 1},
        headers=admin_headers,
    ).json()["token"]

    assert client.get(f"/api/v1/shares/{token}/download").status_code == 200
    # Second download exceeds the limit.
    assert client.get(f"/api/v1/shares/{token}/download").status_code == 403


def test_tagging_and_filtering(client, admin_headers, workspace):
    ws_id = workspace["id"]
    tag = client.post(
        f"/api/v1/workspaces/{ws_id}/tags",
        json={"name": "hero", "color": "#0f766e"},
        headers=admin_headers,
    ).json()
    asset = _upload(client, ws_id, admin_headers).json()

    tagged = client.put(
        f"/api/v1/workspaces/{ws_id}/assets/{asset['id']}/tags",
        json={"tag_ids": [tag["id"]]},
        headers=admin_headers,
    )
    assert tagged.status_code == 200
    assert tagged.json()["tags"][0]["name"] == "hero"

    filtered = client.get(
        f"/api/v1/workspaces/{ws_id}/assets",
        params={"tag_ids": tag["id"]},
        headers=admin_headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
