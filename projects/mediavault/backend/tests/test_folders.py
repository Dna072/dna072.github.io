"""Folder hierarchy tests."""

from __future__ import annotations


def _folder(client, ws_id, headers, name, parent_id=None):
    body = {"name": name}
    if parent_id:
        body["parent_id"] = parent_id
    return client.post(f"/api/v1/workspaces/{ws_id}/folders", json=body, headers=headers)


def test_folder_tree_and_paths(client, admin_headers, workspace):
    ws_id = workspace["id"]
    marketing = _folder(client, ws_id, admin_headers, "Marketing").json()
    q1 = _folder(client, ws_id, admin_headers, "Q1", marketing["id"]).json()
    assert q1["path"] == "/Marketing/Q1"

    tree = client.get(f"/api/v1/workspaces/{ws_id}/folders", headers=admin_headers).json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Marketing"
    assert tree[0]["children"][0]["name"] == "Q1"


def test_breadcrumbs(client, admin_headers, workspace):
    ws_id = workspace["id"]
    a = _folder(client, ws_id, admin_headers, "A").json()
    b = _folder(client, ws_id, admin_headers, "B", a["id"]).json()
    crumbs = client.get(
        f"/api/v1/workspaces/{ws_id}/folders/{b['id']}/breadcrumbs", headers=admin_headers
    ).json()
    assert [c["name"] for c in crumbs] == ["A", "B"]


def test_duplicate_folder_name_conflict(client, admin_headers, workspace):
    ws_id = workspace["id"]
    _folder(client, ws_id, admin_headers, "Dupe")
    resp = _folder(client, ws_id, admin_headers, "Dupe")
    assert resp.status_code == 409


def test_move_folder_repaths_descendants(client, admin_headers, workspace):
    ws_id = workspace["id"]
    a = _folder(client, ws_id, admin_headers, "A").json()
    b = _folder(client, ws_id, admin_headers, "B").json()
    child = _folder(client, ws_id, admin_headers, "Child", a["id"]).json()

    moved = client.patch(
        f"/api/v1/workspaces/{ws_id}/folders/{child['id']}",
        json={"parent_id": b["id"]},
        headers=admin_headers,
    )
    assert moved.status_code == 200
    assert moved.json()["path"] == "/B/Child"


def test_cannot_move_into_own_descendant(client, admin_headers, workspace):
    ws_id = workspace["id"]
    a = _folder(client, ws_id, admin_headers, "A").json()
    child = _folder(client, ws_id, admin_headers, "Child", a["id"]).json()
    resp = client.patch(
        f"/api/v1/workspaces/{ws_id}/folders/{a['id']}",
        json={"parent_id": child["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 422
