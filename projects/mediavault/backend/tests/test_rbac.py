import pytest


@pytest.fixture
def workspace_with_roles(client, register_user, auth_headers, make_workspace):
    """Owner (ADMIN), a MEMBER, and a VIEWER all in the same workspace."""
    owner_tokens = register_user(client, email="rbac-owner@example.com")
    owner_headers = auth_headers(owner_tokens)
    workspace = make_workspace(client, owner_headers)

    member_tokens = register_user(client, email="rbac-member@example.com")
    client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        json={"email": "rbac-member@example.com", "role": "MEMBER"},
        headers=owner_headers,
    )

    viewer_tokens = register_user(client, email="rbac-viewer@example.com")
    client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        json={"email": "rbac-viewer@example.com", "role": "VIEWER"},
        headers=owner_headers,
    )

    return {
        "workspace": workspace,
        "owner_headers": owner_headers,
        "member_headers": auth_headers(member_tokens),
        "viewer_headers": auth_headers(viewer_tokens),
    }


def test_viewer_cannot_create_folder(client, workspace_with_roles):
    ws_id = workspace_with_roles["workspace"]["id"]
    response = client.post(
        f"/api/v1/workspaces/{ws_id}/folders",
        json={"name": "Nope"},
        headers=workspace_with_roles["viewer_headers"],
    )
    assert response.status_code == 403


def test_member_can_create_folder(client, workspace_with_roles):
    ws_id = workspace_with_roles["workspace"]["id"]
    response = client.post(
        f"/api/v1/workspaces/{ws_id}/folders",
        json={"name": "Yes"},
        headers=workspace_with_roles["member_headers"],
    )
    assert response.status_code == 201


def test_viewer_can_list_but_not_write(client, workspace_with_roles):
    ws_id = workspace_with_roles["workspace"]["id"]
    list_response = client.get(
        f"/api/v1/workspaces/{ws_id}/folders", headers=workspace_with_roles["viewer_headers"]
    )
    assert list_response.status_code == 200

    tag_response = client.post(
        f"/api/v1/workspaces/{ws_id}/tags",
        json={"name": "cannot-create"},
        headers=workspace_with_roles["viewer_headers"],
    )
    assert tag_response.status_code == 403


def test_member_cannot_update_workspace_settings(client, workspace_with_roles):
    ws_id = workspace_with_roles["workspace"]["id"]
    response = client.patch(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Renamed"},
        headers=workspace_with_roles["member_headers"],
    )
    assert response.status_code == 403


def test_admin_can_update_workspace_settings(client, workspace_with_roles):
    ws_id = workspace_with_roles["workspace"]["id"]
    response = client.patch(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Renamed"},
        headers=workspace_with_roles["owner_headers"],
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_member_cannot_delete_others_asset_but_admin_can(client, workspace_with_roles):
    ws_id = workspace_with_roles["workspace"]["id"]
    owner_headers = workspace_with_roles["owner_headers"]
    member_headers = workspace_with_roles["member_headers"]

    upload = client.post(
        f"/api/v1/workspaces/{ws_id}/assets",
        files={"file": ("owner.mp4", b"owner-owned-bytes", "video/mp4")},
        headers=owner_headers,
    )
    assert upload.status_code == 201
    asset_id = upload.json()["id"]

    forbidden = client.delete(
        f"/api/v1/workspaces/{ws_id}/assets/{asset_id}", headers=member_headers
    )
    assert forbidden.status_code == 403

    allowed = client.delete(
        f"/api/v1/workspaces/{ws_id}/assets/{asset_id}", headers=owner_headers
    )
    assert allowed.status_code == 200
