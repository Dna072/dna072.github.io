def test_create_and_get_workspace(client, register_user, auth_headers, make_workspace):
    tokens = register_user(client, email="owner@example.com")
    headers = auth_headers(tokens)
    workspace = make_workspace(client, headers, name="Creative Team")
    assert workspace["name"] == "Creative Team"
    assert workspace["my_role"] == "ADMIN"
    assert workspace["member_count"] == 1

    response = client.get(f"/api/v1/workspaces/{workspace['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == workspace["id"]


def test_duplicate_slug_rejected(client, register_user, auth_headers):
    tokens = register_user(client, email="owner2@example.com")
    headers = auth_headers(tokens)
    client.post(
        "/api/v1/workspaces", json={"name": "A", "slug": "same-slug"}, headers=headers
    )
    response = client.post(
        "/api/v1/workspaces", json={"name": "B", "slug": "same-slug"}, headers=headers
    )
    assert response.status_code == 409


def test_invalid_slug_rejected(client, register_user, auth_headers):
    tokens = register_user(client, email="owner3@example.com")
    headers = auth_headers(tokens)
    response = client.post(
        "/api/v1/workspaces", json={"name": "A", "slug": "Not A Slug!"}, headers=headers
    )
    assert response.status_code == 422


def test_non_member_cannot_access_workspace(client, register_user, auth_headers, make_workspace):
    owner_tokens = register_user(client, email="owner4@example.com")
    workspace = make_workspace(client, auth_headers(owner_tokens))

    stranger_tokens = register_user(client, email="stranger@example.com")
    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}", headers=auth_headers(stranger_tokens)
    )
    assert response.status_code == 404


def test_invite_member_and_list(client, register_user, auth_headers, make_workspace):
    owner_tokens = register_user(client, email="owner5@example.com")
    owner_headers = auth_headers(owner_tokens)
    workspace = make_workspace(client, owner_headers)

    register_user(client, email="member5@example.com")
    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        json={"email": "member5@example.com", "role": "MEMBER"},
        headers=owner_headers,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "MEMBER"

    members_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members", headers=owner_headers
    )
    assert members_response.status_code == 200
    assert len(members_response.json()) == 2


def test_non_admin_cannot_invite_members(client, register_user, auth_headers, make_workspace):
    owner_tokens = register_user(client, email="owner6@example.com")
    owner_headers = auth_headers(owner_tokens)
    workspace = make_workspace(client, owner_headers)

    member_tokens = register_user(client, email="member6@example.com")
    client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        json={"email": "member6@example.com", "role": "MEMBER"},
        headers=owner_headers,
    )

    register_user(client, email="target6@example.com")
    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        json={"email": "target6@example.com", "role": "VIEWER"},
        headers=auth_headers(member_tokens),
    )
    assert response.status_code == 403


def test_cannot_demote_or_remove_owner(client, register_user, auth_headers, make_workspace):
    owner_tokens = register_user(client, email="owner7@example.com")
    owner_headers = auth_headers(owner_tokens)
    workspace = make_workspace(client, owner_headers)

    members = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members", headers=owner_headers
    ).json()
    owner_membership_id = members[0]["id"]

    demote_response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/members/{owner_membership_id}",
        json={"role": "VIEWER"},
        headers=owner_headers,
    )
    assert demote_response.status_code == 400

    remove_response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{owner_membership_id}",
        headers=owner_headers,
    )
    assert remove_response.status_code == 400
