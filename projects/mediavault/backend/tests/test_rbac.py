"""RBAC and workspace membership tests."""

from __future__ import annotations

from tests.conftest import auth_headers


def test_owner_is_admin(client, admin_headers, workspace):
    resp = client.get(f"/api/v1/workspaces/{workspace['id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMIN"


def test_non_member_cannot_access_workspace(client, admin_headers, workspace):
    outsider = auth_headers(client, "outsider@example.com")
    resp = client.get(f"/api/v1/workspaces/{workspace['id']}", headers=outsider)
    assert resp.status_code == 404  # existence hidden from non-members


def test_viewer_cannot_upload_but_can_read(client, admin_headers, workspace):
    ws_id = workspace["id"]
    # Register a viewer and add them to the workspace.
    auth_headers(client, "viewer@example.com")
    add = client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "viewer@example.com", "role": "VIEWER"},
        headers=admin_headers,
    )
    assert add.status_code == 201

    viewer_headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@example.com", "password": "Password123!"},
        ).json()["tokens"]["access_token"]
    }

    # Viewer can list assets (read).
    assert client.get(f"/api/v1/workspaces/{ws_id}/assets", headers=viewer_headers).status_code == 200

    # Viewer cannot create a folder (write requires MEMBER).
    resp = client.post(
        f"/api/v1/workspaces/{ws_id}/folders",
        json={"name": "Nope"},
        headers=viewer_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"


def test_member_cannot_manage_members(client, admin_headers, workspace):
    ws_id = workspace["id"]
    auth_headers(client, "member@example.com")
    client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "member@example.com", "role": "MEMBER"},
        headers=admin_headers,
    )
    member_headers = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            json={"email": "member@example.com", "password": "Password123!"},
        ).json()["tokens"]["access_token"]
    }
    # MEMBER cannot invite others (ADMIN only).
    resp = client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "member@example.com", "role": "MEMBER"},
        headers=member_headers,
    )
    assert resp.status_code == 403


def test_admin_can_change_role(client, admin_headers, workspace):
    ws_id = workspace["id"]
    auth_headers(client, "promote@example.com")
    add = client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "promote@example.com", "role": "VIEWER"},
        headers=admin_headers,
    ).json()
    resp = client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{add['id']}",
        json={"role": "ADMIN"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMIN"


def test_owner_role_cannot_be_downgraded(client, admin_headers, workspace):
    ws_id = workspace["id"]
    members = client.get(f"/api/v1/workspaces/{ws_id}/members", headers=admin_headers).json()
    owner_membership = members[0]
    resp = client.patch(
        f"/api/v1/workspaces/{ws_id}/members/{owner_membership['id']}",
        json={"role": "VIEWER"},
        headers=admin_headers,
    )
    assert resp.status_code == 403
