from __future__ import annotations


def test_register_creates_user_and_default_workspace(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "full_name": "Ada Lovelace", "password": "password123"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "a@b.com"
    assert "id" in body

    login = client.post(
        "/api/v1/auth/login", json={"email": "a@b.com", "password": "password123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    ws = client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert ws.status_code == 200
    assert len(ws.json()) == 1  # default workspace was bootstrapped


def test_duplicate_email_conflict(client):
    payload = {"email": "dup@b.com", "full_name": "Dup", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "x@b.com", "full_name": "X", "password": "password123"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": "x@b.com", "password": "nope"})
    assert resp.status_code == 401


def test_refresh_flow(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "r@b.com", "full_name": "R", "password": "password123"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "r@b.com", "password": "password123"}
    ).json()
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_refresh_rejects_access_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "s@b.com", "full_name": "S", "password": "password123"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "s@b.com", "password": "password123"}
    ).json()
    # Passing an access token where a refresh token is expected must fail.
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401
