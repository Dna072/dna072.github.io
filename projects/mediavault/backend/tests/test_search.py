import pytest


@pytest.fixture
def ws(client, register_user, auth_headers, make_workspace):
    tokens = register_user(client, email="search-owner@example.com")
    headers = auth_headers(tokens)
    workspace = make_workspace(client, headers)
    return {"id": workspace["id"], "headers": headers}


def _upload(client, ws, filename, description=""):
    return client.post(
        f"/api/v1/workspaces/{ws['id']}/assets?description={description}",
        files={"file": (filename, b"video-bytes", "video/mp4")},
        headers=ws["headers"],
    ).json()


def test_search_finds_by_filename(client, ws):
    _upload(client, ws, "brand_launch_teaser.mp4")
    _upload(client, ws, "unrelated_bts_footage.mp4")

    response = client.get(f"/api/v1/workspaces/{ws['id']}/search?q=launch", headers=ws["headers"])
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "brand_launch_teaser.mp4"
    assert body["items"][0]["rank"] is not None


def test_search_finds_by_description(client, ws):
    _upload(client, ws, "clip_a.mp4", description="Q4%20quarterly%20highlights%20reel")
    response = client.get(
        f"/api/v1/workspaces/{ws['id']}/search?q=quarterly", headers=ws["headers"]
    )
    assert response.json()["total"] == 1


def test_search_no_query_falls_back_to_browse(client, ws):
    _upload(client, ws, "one.mp4")
    _upload(client, ws, "two.mp4")
    response = client.get(f"/api/v1/workspaces/{ws['id']}/search", headers=ws["headers"])
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_search_no_results_for_unmatched_query(client, ws):
    _upload(client, ws, "one.mp4")
    response = client.get(
        f"/api/v1/workspaces/{ws['id']}/search?q=zzzznomatchzzzz", headers=ws["headers"]
    )
    assert response.json()["total"] == 0


def test_search_scoped_to_workspace(client, register_user, auth_headers, make_workspace):
    tokens_a = register_user(client, email="search-a@example.com")
    headers_a = auth_headers(tokens_a)
    ws_a = make_workspace(client, headers_a)
    client.post(
        f"/api/v1/workspaces/{ws_a['id']}/assets",
        files={"file": ("shared_keyword_video.mp4", b"bytes", "video/mp4")},
        headers=headers_a,
    )

    tokens_b = register_user(client, email="search-b@example.com")
    headers_b = auth_headers(tokens_b)
    ws_b = make_workspace(client, headers_b)

    response = client.get(
        f"/api/v1/workspaces/{ws_b['id']}/search?q=keyword", headers=headers_b
    )
    assert response.json()["total"] == 0


def test_search_filter_by_tag(client, ws):
    asset = _upload(client, ws, "footage.mp4")
    tag = client.post(
        f"/api/v1/workspaces/{ws['id']}/tags", json={"name": "raw"}, headers=ws["headers"]
    ).json()
    client.post(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset['id']}/tags/{tag['id']}",
        headers=ws["headers"],
    )
    response = client.get(
        f"/api/v1/workspaces/{ws['id']}/search?tag=raw", headers=ws["headers"]
    )
    assert response.json()["total"] == 1
