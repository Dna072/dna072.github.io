"""Search, filtering, sorting and pagination tests."""

from __future__ import annotations

import io

from tests.test_assets import PNG_1x1


def _upload(client, ws_id, headers, name, description="", folder_id=None):
    data = {"name": name, "description": description}
    if folder_id:
        data["folder_id"] = folder_id
    return client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        headers=headers,
        files={"file": (f"{name}.png", io.BytesIO(PNG_1x1), "image/png")},
        data=data,
    )


def test_pagination_envelope(client, admin_headers, workspace):
    ws_id = workspace["id"]
    for i in range(25):
        _upload(client, ws_id, admin_headers, name=f"Asset {i:02d}")

    page1 = client.get(
        f"/api/v1/workspaces/{ws_id}/assets",
        params={"page": 1, "page_size": 10},
        headers=admin_headers,
    ).json()
    assert page1["total"] == 25
    assert page1["pages"] == 3
    assert len(page1["items"]) == 10

    page3 = client.get(
        f"/api/v1/workspaces/{ws_id}/assets",
        params={"page": 3, "page_size": 10},
        headers=admin_headers,
    ).json()
    assert len(page3["items"]) == 5


def test_sorting_by_name_asc(client, admin_headers, workspace):
    ws_id = workspace["id"]
    for name in ["Zebra", "Alpha", "Mango"]:
        _upload(client, ws_id, admin_headers, name=name)
    resp = client.get(
        f"/api/v1/workspaces/{ws_id}/assets",
        params={"sort_by": "name", "sort_dir": "asc"},
        headers=admin_headers,
    ).json()
    names = [a["name"] for a in resp["items"]]
    assert names == ["Alpha", "Mango", "Zebra"]


def test_search_matches_name_and_description(client, admin_headers, workspace):
    ws_id = workspace["id"]
    _upload(client, ws_id, admin_headers, name="Summer Campaign", description="beach sunset promo")
    _upload(client, ws_id, admin_headers, name="Winter Recap", description="snow highlights")

    resp = client.get(
        f"/api/v1/workspaces/{ws_id}/search",
        params={"q": "sunset"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"]["total"] == 1
    assert body["results"]["items"][0]["name"] == "Summer Campaign"
    assert "IMAGE" in body["facets"]["kinds"]


def test_search_no_results(client, admin_headers, workspace):
    ws_id = workspace["id"]
    _upload(client, ws_id, admin_headers, name="Product Demo")
    resp = client.get(
        f"/api/v1/workspaces/{ws_id}/search",
        params={"q": "nonexistentterm"},
        headers=admin_headers,
    ).json()
    assert resp["results"]["total"] == 0


def test_filter_by_folder_and_subfolders(client, admin_headers, workspace):
    ws_id = workspace["id"]
    parent = client.post(
        f"/api/v1/workspaces/{ws_id}/folders", json={"name": "Campaigns"}, headers=admin_headers
    ).json()
    child = client.post(
        f"/api/v1/workspaces/{ws_id}/folders",
        json={"name": "2026", "parent_id": parent["id"]},
        headers=admin_headers,
    ).json()

    _upload(client, ws_id, admin_headers, name="Root asset")
    _upload(client, ws_id, admin_headers, name="Parent asset", folder_id=parent["id"])
    _upload(client, ws_id, admin_headers, name="Child asset", folder_id=child["id"])

    only_parent = client.get(
        f"/api/v1/workspaces/{ws_id}/assets",
        params={"folder_id": parent["id"]},
        headers=admin_headers,
    ).json()
    assert only_parent["total"] == 1

    with_sub = client.get(
        f"/api/v1/workspaces/{ws_id}/assets",
        params={"folder_id": parent["id"], "include_subfolders": True},
        headers=admin_headers,
    ).json()
    assert with_sub["total"] == 2
