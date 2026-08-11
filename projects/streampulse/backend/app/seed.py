"""Seed the database with realistic — but clearly synthetic — analytics data.

This generates several months of impression and view events with plausible
structure: per-video popularity, recency decay, weekly seasonality (weekends
run hotter), geo/device mixes, and retention/engagement that correlate with a
per-video "quality" factor.

NONE OF THIS IS REAL TRAFFIC. It exists only so the dashboard has something
meaningful to render locally. Run with::

    python -m app.seed

Environment knobs:
    SEED_DAYS         number of days of history to generate (default 120)
    SEED_TRAFFIC      global multiplier on volume (default 1.0)
    SEED_RANDOM_SEED  RNG seed for reproducibility (default 42)
"""

import os
import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models.analytics import ImpressionEvent, Video, ViewEvent
from app.models.user import User

configure_logging(settings.log_level, json_logs=False)
log = get_logger("seed")

BATCH = 5000

CATEGORIES = [
    "Tutorials",
    "Product Demos",
    "Live Streams",
    "Shorts",
    "Interviews",
    "Behind the Scenes",
]

# (title, category, duration_seconds)
VIDEO_LIBRARY = [
    ("Getting Started with StreamPulse", "Tutorials", 480),
    ("Advanced Query Optimization", "Tutorials", 1020),
    ("Building Your First Dashboard", "Tutorials", 720),
    ("Indexing Strategies Explained", "Tutorials", 900),
    ("StreamPulse 2.0 Product Tour", "Product Demos", 360),
    ("Comparison Mode Deep Dive", "Product Demos", 540),
    ("Audience Insights Walkthrough", "Product Demos", 420),
    ("Realtime Ingestion Demo", "Product Demos", 300),
    ("Launch Day Live Q&A", "Live Streams", 3600),
    ("Engineering Office Hours", "Live Streams", 2700),
    ("Roadmap Live: What's Next", "Live Streams", 1800),
    ("60-Second Metrics Tip", "Shorts", 60),
    ("Funnel Analysis in 90s", "Shorts", 90),
    ("One SQL Trick", "Shorts", 45),
    ("Retention, Fast", "Shorts", 75),
    ("Interview: Scaling Analytics", "Interviews", 1500),
    ("Interview: From Batch to Streaming", "Interviews", 1320),
    ("Interview: A Day in Data Eng", "Interviews", 1140),
    ("How We Built the Query Layer", "Behind the Scenes", 660),
    ("Designing the Charts", "Behind the Scenes", 600),
    ("Load Testing StreamPulse", "Behind the Scenes", 780),
    ("Our On-Call Playbook", "Behind the Scenes", 540),
    ("Data Modeling for Video", "Tutorials", 840),
    ("Cohorts & Segmentation", "Product Demos", 480),
]

COUNTRY_WEIGHTS = {
    "US": 30, "GB": 12, "DE": 9, "IN": 9, "FR": 7, "BR": 6,
    "CA": 6, "NG": 5, "GH": 4, "JP": 4, "AU": 4, "ZA": 4,
}
DEVICE_WEIGHTS = {"mobile": 52, "desktop": 30, "tablet": 10, "tv": 8}


def _weighted_keys(weights: dict[str, int]) -> tuple[list[str], list[int]]:
    return list(weights.keys()), list(weights.values())


def _chunked_insert(db: Session, model, rows: list[dict]) -> int:
    total = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        db.execute(model.__table__.insert(), chunk)
        total += len(chunk)
    return total


def reset(db: Session) -> None:
    db.execute(delete(ViewEvent))
    db.execute(delete(ImpressionEvent))
    db.execute(delete(Video))
    db.commit()
    log.info("cleared_existing_event_data")


def ensure_admin(db: Session) -> None:
    existing = db.execute(
        select(User).where(User.email == settings.seed_admin_email)
    ).scalar_one_or_none()
    if existing:
        log.info("admin_exists", email=settings.seed_admin_email)
        return
    db.add(
        User(
            email=settings.seed_admin_email,
            full_name="StreamPulse Demo",
            hashed_password=hash_password(settings.seed_admin_password),
            is_active=True,
        )
    )
    db.commit()
    log.info("admin_created", email=settings.seed_admin_email)


def create_videos(db: Session, now: datetime, days: int) -> list[dict]:
    videos: list[Video] = []
    for idx, (title, category, duration) in enumerate(VIDEO_LIBRARY):
        # Spread publish dates across (and a bit before) the window.
        age_days = random.randint(5, days + 60)
        published = now - timedelta(days=age_days, hours=random.randint(0, 23))
        videos.append(
            Video(
                title=title,
                category=category,
                duration_seconds=duration,
                published_at=published,
                thumbnail_url=f"https://picsum.photos/seed/sp{idx}/320/180",
            )
        )
    db.add_all(videos)
    db.commit()
    for v in videos:
        db.refresh(v)

    # Attach synthetic latent traits used by the generator.
    meta = []
    for v in videos:
        meta.append(
            {
                "id": v.id,
                "duration": v.duration_seconds,
                "published_at": v.published_at,
                "popularity": random.uniform(0.4, 3.0),  # base daily draw scale
                "quality": random.uniform(0.45, 0.95),  # retention/engagement driver
            }
        )
    log.info("videos_created", count=len(videos))
    return meta


def generate_events(
    db: Session, meta: list[dict], now: datetime, days: int, traffic: float
) -> None:
    countries, c_weights = _weighted_keys(COUNTRY_WEIGHTS)
    devices, d_weights = _weighted_keys(DEVICE_WEIGHTS)

    # A bounded pool of pseudonymous viewers so that repeat views exist and
    # "unique viewers" is meaningfully smaller than "total views". A small
    # subset are power viewers (sampled far more often).
    pool_size = max(500, int(6000 * traffic))
    viewer_pool = [str(uuid.uuid4()) for _ in range(pool_size)]
    power = viewer_pool[: max(1, pool_size // 20)]

    def pick_viewer() -> str:
        # ~35% of views come from the power-viewer subset.
        if random.random() < 0.35:
            return random.choice(power)
        return random.choice(viewer_pool)

    impressions: list[dict] = []
    views: list[dict] = []
    total_views = 0
    total_impr = 0

    window_start = now - timedelta(days=days)

    for day_offset in range(days):
        day = window_start + timedelta(days=day_offset)
        # Weekly seasonality: weekends busier; slight upward trend over time.
        weekday = day.weekday()
        weekend_boost = 1.35 if weekday >= 5 else 1.0
        trend = 1.0 + 0.3 * (day_offset / max(days, 1))

        for m in meta:
            # Videos published after this day generate nothing yet.
            if m["published_at"].date() > day.date():
                continue
            # Recency decay: interest fades after publish.
            age = max((day.date() - m["published_at"].date()).days, 0)
            recency = 1.0 / (1.0 + age / 21.0)

            expected_impr = (
                m["popularity"] * 220 * recency * weekend_boost * trend * traffic
            )
            day_impr = max(0, int(random.gauss(expected_impr, expected_impr * 0.25)))
            if day_impr == 0:
                continue

            # Click-through from impression to view.
            ctr = min(0.6, max(0.08, random.gauss(0.28, 0.06)))
            day_views = int(day_impr * ctr)

            for _ in range(day_impr):
                ts = day + timedelta(
                    seconds=random.randint(0, 86399)
                )
                impressions.append(
                    {
                        "video_id": m["id"],
                        "event_time": ts,
                        "country_code": random.choices(countries, c_weights)[0],
                        "device_type": random.choices(devices, d_weights)[0],
                    }
                )
            total_impr += day_impr

            for _ in range(day_views):
                ts = day + timedelta(seconds=random.randint(0, 86399))
                device = random.choices(devices, d_weights)[0]
                # Retention fraction of the video watched, skewed by quality.
                # Beta-ish: quality shifts the mean watched fraction.
                base = random.betavariate(2.0, 2.2)
                watched_frac = min(1.0, base * (0.6 + m["quality"]))
                # TVs/desktops watch a little longer than mobile on average.
                if device in ("tv", "desktop"):
                    watched_frac = min(1.0, watched_frac * 1.1)
                watch_seconds = int(m["duration"] * watched_frac)
                quartile = min(4, int(watched_frac * 4 + 1e-9))
                if watched_frac >= 0.98:
                    quartile = 4

                # Engagement more likely with higher quality and deeper watch.
                eng_p = m["quality"] * (0.15 + 0.6 * watched_frac)
                liked = random.random() < eng_p * 0.5
                commented = random.random() < eng_p * 0.12
                shared = random.random() < eng_p * 0.08

                views.append(
                    {
                        "video_id": m["id"],
                        "viewer_id": pick_viewer(),
                        "event_time": ts,
                        "country_code": random.choices(countries, c_weights)[0],
                        "device_type": device,
                        "watch_seconds": watch_seconds,
                        "quartile_reached": quartile,
                        "liked": liked,
                        "commented": commented,
                        "shared": shared,
                    }
                )
            total_views += day_views

            # Flush periodically to keep memory bounded.
            if len(views) >= BATCH * 4:
                _chunked_insert(db, ViewEvent, views)
                _chunked_insert(db, ImpressionEvent, impressions)
                db.commit()
                views.clear()
                impressions.clear()

    if views:
        _chunked_insert(db, ViewEvent, views)
    if impressions:
        _chunked_insert(db, ImpressionEvent, impressions)
    db.commit()
    log.info("events_generated", views=total_views, impressions=total_impr, days=days)


def main() -> None:
    days = int(os.getenv("SEED_DAYS", "120"))
    traffic = float(os.getenv("SEED_TRAFFIC", "1.0"))
    seed = int(os.getenv("SEED_RANDOM_SEED", "42"))
    random.seed(seed)

    now = datetime.now(UTC)
    log.info(
        "seed_start",
        days=days,
        traffic=traffic,
        database=engine.url.render_as_string(hide_password=True),
    )

    with SessionLocal() as db:
        ensure_admin(db)
        reset(db)
        meta = create_videos(db, now, days)
        generate_events(db, meta, now, days, traffic)

    log.info("seed_done")


if __name__ == "__main__":
    main()
