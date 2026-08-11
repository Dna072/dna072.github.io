def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "up"


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["api_prefix"] == "/api/v1"
