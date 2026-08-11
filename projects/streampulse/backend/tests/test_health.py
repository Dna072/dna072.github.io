def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


def test_request_id_header(client):
    r = client.get("/health")
    assert r.headers.get("X-Request-ID")


def test_request_id_echoed(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers.get("X-Request-ID") == "abc123"
