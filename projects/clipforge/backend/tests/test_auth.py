"""Authentication API tests."""

from __future__ import annotations


def _register(client, email="user@example.com", password="password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )


def test_register_returns_user_and_tokens(client):
    resp = _register(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


def test_register_duplicate_email_conflicts(client):
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "x@example.com", "password": "short", "full_name": "X"},
    )
    assert resp.status_code == 422


def test_login_success_and_failure(client):
    _register(client, email="login@example.com", password="mypassword1")

    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "mypassword1"},
    )
    assert ok.status_code == 200
    assert ok.json()["tokens"]["access_token"]

    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrongpass"},
    )
    assert bad.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_current_user(client):
    tokens = _register(client, email="me@example.com").json()["tokens"]
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_refresh_token_rotates_access(client):
    tokens = _register(client, email="refresh@example.com").json()["tokens"]
    resp = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_rejects_access_token(client):
    tokens = _register(client, email="wrong@example.com").json()["tokens"]
    # Using an access token where a refresh token is expected must fail.
    resp = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert resp.status_code == 401
