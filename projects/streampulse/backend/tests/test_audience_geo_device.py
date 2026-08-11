def test_funnel_stages_and_percentages(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    response = client.get(
        "/api/audience/funnel",
        params={"start": today.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    stages = {s["stage"]: s for s in response.json()["stages"]}

    assert stages["play"]["count"] == 4
    assert stages["play"]["percent_of_plays"] == 100.0
    assert stages["reach_25"]["count"] == 4
    assert stages["reach_50"]["count"] == 3
    assert stages["reach_75"]["count"] == 2
    assert stages["complete"]["count"] == 2
    assert stages["complete"]["percent_of_plays"] == 50.0


def test_funnel_empty_range_has_zeroed_stages(client, auth_headers, seeded_videos):
    response = client.get(
        "/api/audience/funnel",
        params={"start": "2000-01-01", "end": "2000-01-02"},
        headers=auth_headers,
    )
    stages = response.json()["stages"]
    assert all(s["count"] == 0 for s in stages)
    assert all(s["percent_of_plays"] == 0.0 for s in stages)


def test_audience_devices_and_referrers(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    response = client.get(
        "/api/audience",
        params={"start": today.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    devices = {d["device_type"]: d for d in body["devices"]}
    assert devices["mobile"]["views"] == 2
    assert devices["desktop"]["views"] == 1
    assert devices["tv"]["views"] == 1
    assert devices["mobile"]["share_percent"] == 50.0

    referrers = {r["referrer_source"]: r for r in body["referrers"]}
    assert referrers["search"]["views"] == 1
    assert referrers["embed"]["views"] == 1


def test_device_endpoint_matches_audience_devices(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    response = client.get(
        "/api/device",
        params={"start": today.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    items = {d["device_type"]: d for d in response.json()["items"]}
    assert items["mobile"]["views"] == 2
    assert items["tv"]["views"] == 1


def test_geo_breakdown(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    response = client.get(
        "/api/geo",
        params={"start": today.isoformat(), "end": today.isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200
    items = {i["country_code"]: i for i in response.json()["items"]}
    assert items["US"]["views"] == 2
    assert items["US"]["share_percent"] == 50.0
    assert items["GB"]["views"] == 1
    assert items["DE"]["views"] == 1
    assert items["DE"]["country_name"] == "Germany"


def test_geo_and_device_respect_video_filter(client, auth_headers, seeded_videos):
    today = seeded_videos["today"]
    video_b = seeded_videos["video_b"]
    response = client.get(
        "/api/geo",
        params={"start": today.isoformat(), "end": today.isoformat(), "video_id": video_b.id},
        headers=auth_headers,
    )
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["country_code"] == "DE"
