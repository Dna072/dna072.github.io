"""Authentication, token refresh and rotation tests."""

from __future__ import annotations


def test_register_and_login(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "jane@example.com", "password": "Password123!", "full_name": "Jane"},
    )
    assert reg.status_code == 201
    tokens = reg.json()["tokens"]
    assert tokens["access_token"] and tokens["refresh_token"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "jane@example.com"


def test_duplicate_registration_conflicts(client):
    payload = {"email": "dup@example.com", "password": "Password123!"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_login_wrong_password_rejected(client):
    client.post("/api/v1/auth/register", json={"email": "bob@example.com", "password": "Password123!"})
    resp = client.post(
        "/api/v1/auth/login", json={"email": "bob@example.com", "password": "wrong-password"}
    )
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_current_user(client):
    reg = client.post(
        "/api/v1/auth/register", json={"email": "me@example.com", "password": "Password123!"}
    ).json()
    headers = {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_refresh_rotates_token(client):
    reg = client.post(
        "/api/v1/auth/register", json={"email": "rot@example.com", "password": "Password123!"}
    ).json()
    refresh = reg["tokens"]["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert first.status_code == 200
    new_refresh = first.json()["refresh_token"]
    assert new_refresh != refresh

    # Old refresh token is now revoked (rotation).
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert replay.status_code == 401


def test_logout_revokes_refresh(client):
    reg = client.post(
        "/api/v1/auth/register", json={"email": "out@example.com", "password": "Password123!"}
    ).json()
    refresh = reg["tokens"]["refresh_token"]
    assert client.post("/api/v1/auth/logout", json={"refresh_token": refresh}).status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_invalid_token_rejected(client):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
