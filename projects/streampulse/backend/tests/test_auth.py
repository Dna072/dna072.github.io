def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "new@streampulse.io", "password": "supersecure1", "full_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "new@streampulse.io"
    assert body["user"]["full_name"] == "New User"


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@streampulse.io", "password": "supersecure1", "full_name": "Dup"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "short@streampulse.io", "password": "short", "full_name": "Short"},
    )
    assert response.status_code == 422


def test_login_success(client, test_user):
    response = client.post(
        "/api/auth/login", json={"email": "tester@streampulse.io", "password": "testpassword123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "tester@streampulse.io"


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/api/auth/login", json={"email": "tester@streampulse.io", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post(
        "/api/auth/login", json={"email": "ghost@streampulse.io", "password": "whatever123"}
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "tester@streampulse.io"


def test_me_rejects_garbage_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
