from datetime import timedelta


def test_list_videos_returns_catalogue(client, auth_headers, seeded_videos):
    response = client.get("/api/videos", headers=auth_headers)
    assert response.status_code == 200
    titles = {v["title"] for v in response.json()}
    assert "Deterministic Video A" in titles
    assert "Deterministic Video B" in titles


def test_video_performance_sorted_by_views_desc(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    start = today - timedelta(days=1)
    response = client.get(
        "/api/videos/performance",
        params={"start": start.isoformat(), "end": today.isoformat(), "sort": "views", "order": "desc"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    items = body["items"]
    assert items[0]["title"] == "Deterministic Video A"
    assert items[0]["views"] == 4
    assert items[1]["title"] == "Deterministic Video B"
    assert items[1]["views"] == 1


def test_video_performance_respects_video_filter(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    start = today - timedelta(days=1)
    video_b = seeded_videos["video_b"]
    response = client.get(
        "/api/videos/performance",
        params={"start": start.isoformat(), "end": today.isoformat(), "video_id": video_b.id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Deterministic Video B"
    assert body["items"][0]["views"] == 1


def test_video_performance_pagination(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    start = today - timedelta(days=1)
    response = client.get(
        "/api/videos/performance",
        params={"start": start.isoformat(), "end": today.isoformat(), "limit": 1, "offset": 1},
        headers=auth_headers,
    )
    body = response.json()
    assert len(body["items"]) == 1
    assert body["total"] == 2


def test_video_detail_returns_metrics(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    video_a = seeded_videos["video_a"]
    response = client.get(
        f"/api/videos/{video_a.id}",
        params={"start": today.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["video"]["title"] == "Deterministic Video A"
    assert body["metrics"]["views"] == 3


def test_video_detail_404_for_unknown_id(client, auth_headers, seeded_videos):
    response = client.get("/api/videos/999999", headers=auth_headers)
    assert response.status_code == 404


def test_videos_require_auth(client):
    assert client.get("/api/videos").status_code == 401
    assert client.get("/api/videos/performance").status_code == 401
