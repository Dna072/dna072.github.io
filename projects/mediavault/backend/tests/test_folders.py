import pytest


@pytest.fixture
def ws(client, register_user, auth_headers, make_workspace):
    tokens = register_user(client, email="folders-owner@example.com")
    headers = auth_headers(tokens)
    workspace = make_workspace(client, headers)
    return {"id": workspace["id"], "headers": headers}


def test_create_root_folder(client, ws):
    response = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders", json={"name": "Root"}, headers=ws["headers"]
    )
    assert response.status_code == 201
    assert response.json()["path"] == ""


def test_nested_folder_path(client, ws):
    root = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders", json={"name": "Root"}, headers=ws["headers"]
    ).json()
    child = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders",
        json={"name": "Child", "parent_id": root["id"]},
        headers=ws["headers"],
    ).json()
    assert child["path"] == root["id"]

    grandchild = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders",
        json={"name": "Grandchild", "parent_id": child["id"]},
        headers=ws["headers"],
    ).json()
    assert grandchild["path"] == f"{root['id']}/{child['id']}"


def test_move_folder_recomputes_descendant_paths(client, ws):
    a = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders", json={"name": "A"}, headers=ws["headers"]
    ).json()
    b = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders", json={"name": "B"}, headers=ws["headers"]
    ).json()
    child = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders",
        json={"name": "Child", "parent_id": a["id"]},
        headers=ws["headers"],
    ).json()

    move_response = client.patch(
        f"/api/v1/workspaces/{ws['id']}/folders/{child['id']}",
        json={"parent_id": b["id"]},
        headers=ws["headers"],
    )
    assert move_response.status_code == 200
    assert move_response.json()["path"] == b["id"]


def test_cannot_move_folder_into_its_own_descendant(client, ws):
    a = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders", json={"name": "A"}, headers=ws["headers"]
    ).json()
    child = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders",
        json={"name": "Child", "parent_id": a["id"]},
        headers=ws["headers"],
    ).json()

    response = client.patch(
        f"/api/v1/workspaces/{ws['id']}/folders/{a['id']}",
        json={"parent_id": child["id"]},
        headers=ws["headers"],
    )
    assert response.status_code == 400


def test_delete_folder_sets_asset_folder_id_null(client, ws):
    folder = client.post(
        f"/api/v1/workspaces/{ws['id']}/folders", json={"name": "Temp"}, headers=ws["headers"]
    ).json()
    upload = client.post(
        f"/api/v1/workspaces/{ws['id']}/assets?folder_id={folder['id']}",
        files={"file": ("a.mp4", b"asset-bytes", "video/mp4")},
        headers=ws["headers"],
    )
    asset_id = upload.json()["id"]

    delete_response = client.delete(
        f"/api/v1/workspaces/{ws['id']}/folders/{folder['id']}", headers=ws["headers"]
    )
    assert delete_response.status_code == 200

    asset_response = client.get(
        f"/api/v1/workspaces/{ws['id']}/assets/{asset_id}", headers=ws["headers"]
    )
    assert asset_response.json()["folder_id"] is None
