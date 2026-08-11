def test_register_and_login(client, register_user, auth_headers):
    tokens = register_user(client, email="alice@example.com")
    assert tokens["user"]["email"] == "alice@example.com"
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    response = client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "alice@example.com"


def test_register_duplicate_email_rejected(client, register_user):
    register_user(client, email="dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123", "full_name": "Dup"},
    )
    assert response.status_code == 409


def test_login_wrong_password_rejected(client, register_user):
    register_user(client, email="bob@example.com")
    response = client.post(
        "/api/v1/auth/login", json={"email": "bob@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_unknown_user_rejected(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    )
    assert response.status_code == 401


def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_token_rotation(client, register_user):
    tokens = register_user(client, email="carol@example.com")
    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Old refresh token was revoked by rotation and cannot be reused.
    reuse_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reuse_response.status_code == 401


def test_logout_revokes_refresh_token(client, register_user):
    tokens = register_user(client, email="dana@example.com")
    logout_response = client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 200

    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 401


def test_password_too_short_rejected(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short", "full_name": "Short"},
    )
    assert response.status_code == 422
