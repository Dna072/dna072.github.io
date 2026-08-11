from tests.conftest import TEST_EMAIL


def test_login_success(client, auth_headers):
    assert auth_headers["Authorization"].startswith("Bearer ")


def test_login_bad_password(client):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": TEST_EMAIL, "password": "wrong"},
    )
    assert r.status_code == 401


def test_me(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == TEST_EMAIL


def test_analytics_requires_auth(client):
    assert client.get("/api/v1/analytics/overview").status_code == 401


def test_invalid_token_rejected(client):
    r = client.get(
        "/api/v1/analytics/overview",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401
