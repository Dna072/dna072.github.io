from tests.conftest import CURRENT_RANGE


def test_overview_counts(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/overview", params=CURRENT_RANGE, headers=auth_headers
    )
    assert r.status_code == 200
    body = r.json()
    # 4 views in the current period, 2 distinct viewers (u1, u2).
    assert body["total_views"]["value"] == 4
    assert body["unique_viewers"]["value"] == 2
    # 2 of 4 views reached quartile 4 -> completion rate 0.5.
    assert body["completion_rate"]["value"] == 0.5
    # 2 of 4 views were liked -> engagement rate 0.5.
    assert body["engagement_rate"]["value"] == 0.5
    assert body["comparison_enabled"] is False
    assert body["total_views"]["previous"] is None


def test_overview_comparison(client, auth_headers):
    params = {**CURRENT_RANGE, "compare": "true"}
    r = client.get("/api/v1/analytics/overview", params=params, headers=auth_headers)
    body = r.json()
    assert body["comparison_enabled"] is True
    # Previous equal-length window (4 days earlier) holds 2 views.
    assert body["total_views"]["previous"] == 2
    assert body["total_views"]["delta_pct"] == 100.0


def test_timeseries_buckets(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/timeseries",
        params={**CURRENT_RANGE, "granularity": "day"},
        headers=auth_headers,
    )
    body = r.json()
    assert body["granularity"] == "day"
    total = sum(p["views"] for p in body["points"])
    assert total == 4


def test_video_performance_sorted_and_paginated(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/videos",
        params={**CURRENT_RANGE, "sort_by": "views", "limit": 1, "offset": 0},
        headers=auth_headers,
    )
    body = r.json()
    assert body["total"] == 2  # two videos had views in the window
    assert len(body["items"]) == 1
    # Alpha has 3 views, Beta 1 -> Alpha ranks first.
    assert body["items"][0]["title"] == "Alpha"
    assert body["items"][0]["views"] == 3


def test_video_filter(client, auth_headers):
    catalog = client.get(
        "/api/v1/analytics/videos/catalog", headers=auth_headers
    ).json()
    beta = next(v for v in catalog if v["title"] == "Beta")
    r = client.get(
        "/api/v1/analytics/overview",
        params={**CURRENT_RANGE, "video_id": beta["id"]},
        headers=auth_headers,
    )
    assert r.json()["total_views"]["value"] == 1


def test_geo_breakdown(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/audience/geo", params=CURRENT_RANGE, headers=auth_headers
    )
    rows = r.json()["rows"]
    us = next(row for row in rows if row["key"] == "US")
    assert us["views"] == 3  # 3 US views in current period
    assert us["label"] == "United States"
    # Shares are relative to all 4 views.
    assert abs(us["share"] - 0.75) < 1e-6


def test_device_breakdown(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/audience/device", params=CURRENT_RANGE, headers=auth_headers
    )
    keys = {row["key"] for row in r.json()["rows"]}
    assert {"mobile", "desktop", "tv"}.issubset(keys)


def test_funnel_monotonic(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/funnel", params=CURRENT_RANGE, headers=auth_headers
    )
    stages = r.json()["stages"]
    counts = [s["count"] for s in stages]
    assert stages[0]["stage"] == "Impressions"
    assert counts[0] == 20  # impressions seeded
    assert counts[1] == 4  # views
    # Funnel is non-increasing.
    assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))


def test_bad_date_range_rejected(client, auth_headers):
    r = client.get(
        "/api/v1/analytics/overview",
        params={"start_date": "2026-06-16", "end_date": "2026-06-12"},
        headers=auth_headers,
    )
    assert r.status_code == 422
