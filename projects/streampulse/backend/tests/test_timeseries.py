from datetime import timedelta


def test_timeseries_fills_gaps_with_zeroed_points(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    start = today - timedelta(days=1)
    response = client.get(
        "/api/metrics/timeseries",
        params={"start": start.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    points = response.json()["points"]
    assert len(points) == 2

    yesterday_point, today_point = points
    assert yesterday_point["date"] == start.isoformat()
    assert yesterday_point["views"] == 1  # the 75%-watch video_a event

    assert today_point["date"] == today.isoformat()
    assert today_point["views"] == 4


def test_timeseries_no_data_returns_full_range_of_zeros(client, auth_headers, seeded_videos):
    response = client.get(
        "/api/metrics/timeseries",
        params={"start": "2000-01-01", "end": "2000-01-03"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    points = response.json()["points"]
    assert len(points) == 3
    assert all(p["views"] == 0 for p in points)
    assert all(p["completion_rate"] == 0.0 for p in points)


def test_timeseries_respects_video_filter(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    video_a = seeded_videos["video_a"]
    response = client.get(
        "/api/metrics/timeseries",
        params={"start": today.isoformat(), "end": today.isoformat(), "video_id": video_a.id},
        headers=auth_headers,
    )
    points = response.json()["points"]
    assert len(points) == 1
    assert points[0]["views"] == 3
