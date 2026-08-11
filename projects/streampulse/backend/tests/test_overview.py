def test_overview_requires_auth(client):
    response = client.get("/api/metrics/overview")
    assert response.status_code == 401


def test_overview_aggregates_across_videos(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    response = client.get(
        "/api/metrics/overview",
        params={"start": today.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    current = response.json()["current"]

    assert current["views"] == 4
    assert current["unique_viewers"] == 4
    assert current["avg_watch_percent"] == 68.75
    assert current["completion_rate"] == 50.0
    assert current["likes"] == 2
    assert current["comments"] == 0
    assert current["shares"] == 0
    assert current["engagement_rate"] == 50.0


def test_overview_filters_by_video(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    video_b = seeded_videos["video_b"]
    response = client.get(
        "/api/metrics/overview",
        params={"start": today.isoformat(), "end": today.isoformat(), "video_id": video_b.id},
        headers=auth_headers,
    )
    current = response.json()["current"]
    assert current["views"] == 1
    assert current["avg_watch_percent"] == 100.0
    assert current["completion_rate"] == 100.0


def test_overview_comparison_period(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    response = client.get(
        "/api/metrics/overview",
        params={"start": today.isoformat(), "end": today.isoformat(), "compare": True},
        headers=auth_headers,
    )
    body = response.json()
    assert body["previous"] is not None
    assert body["deltas"] is not None
    assert body["range"]["compare_start"] is not None


def test_overview_rejects_inverted_range(client, auth_headers):
    response = client.get(
        "/api/metrics/overview",
        params={"start": "2026-01-10", "end": "2026-01-01"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_overview_empty_range_returns_zeroed_kpis(client, auth_headers, seeded_videos):
    response = client.get(
        "/api/metrics/overview",
        params={"start": "2000-01-01", "end": "2000-01-02"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    current = response.json()["current"]
    assert current["views"] == 0
    assert current["completion_rate"] == 0.0
    assert current["engagement_rate"] == 0.0
