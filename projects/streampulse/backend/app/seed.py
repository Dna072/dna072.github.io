"""Generate realistic demo data for StreamPulse.

Run with:

    python -m app.seed            # seed if the videos table is empty
    python -m app.seed --reset    # drop & recreate all tables first

The generator models a believable content lifecycle rather than pure
randomness:

* each video gets a random "popularity" weight (log-normal),
* views spike shortly after a video's publish date and decay to a
  long-tail baseline afterwards,
* weekday traffic is heavier than weekend traffic,
* watch-time follows a beta distribution so most sessions drop off early
  and a smaller share watch to completion,
* engagement (like/comment/share) probability scales with watch percent.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.reference_data import COUNTRIES, REFERRER_SOURCES, VIDEO_CATEGORIES
from app.core.security import hash_password
from app.models import DeviceType, EngagementEvent, EngagementType, User, Video, ViewEvent

settings = get_settings()

DEMO_USER_EMAIL = "demo@streampulse.io"
DEMO_USER_PASSWORD = "streampulse123"

DEVICE_WEIGHTS = {
    DeviceType.mobile: 0.46,
    DeviceType.desktop: 0.34,
    DeviceType.tablet: 0.12,
    DeviceType.tv: 0.08,
}

COUNTRY_WEIGHTS = [0.28, 0.12, 0.09, 0.07, 0.08, 0.06, 0.05, 0.06, 0.05, 0.04, 0.03, 0.03, 0.02, 0.01, 0.01]

REFERRER_WEIGHTS = {
    "search": 0.32,
    "social": 0.24,
    "direct": 0.18,
    "recommendation": 0.14,
    "embed": 0.07,
    "email": 0.05,
}

# Bimodal hour-of-day weighting: a lunchtime bump and a larger evening peak.
HOUR_WEIGHTS = [
    1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 8, 9,
    10, 9, 8, 7, 7, 8, 10, 12, 11, 8, 5, 3,
]

TITLE_TEMPLATES = {
    "Product Updates": ["What's new in {product}", "{product} release notes: {month}", "Inside the {product} roadmap"],
    "Tutorials": ["Getting started with {product}", "Advanced {product} workflows", "{product} in 10 minutes"],
    "Customer Stories": ["How {company} scaled with {product}", "{company}'s journey to production", "Behind {company}'s launch"],
    "Webinars": ["Live Q&A: {product} best practices", "{month} webinar: scaling with {product}", "Ask us anything: {product}"],
    "Behind the Scenes": ["Building {product}: engineering diary", "A day with the {product} team", "How we designed {product}"],
    "Engineering Deep Dives": ["Architecting {product} for scale", "Deep dive: {product} internals", "Performance tuning {product}"],
    "Highlights": ["{month} highlights reel", "Top moments from {product} conf", "Best of {product} community"],
}

PRODUCTS = ["StreamPulse", "the analytics API", "the media pipeline", "the encoder", "the CDN layer", "the player SDK"]
COMPANIES = ["Northwind Media", "Aurora Studios", "Fjord Broadcasting", "Lumen Labs", "Cobalt Films", "Nimbus Sports"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _weighted_choice(options: list, weights: list[float]):
    return random.choices(options, weights=weights, k=1)[0]


def _random_title(category: str) -> str:
    template = random.choice(TITLE_TEMPLATES[category])
    return template.format(
        product=random.choice(PRODUCTS),
        company=random.choice(COMPANIES),
        month=random.choice(MONTHS),
    )


def _make_videos(n: int, window_days: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    videos = []
    for i in range(n):
        category = VIDEO_CATEGORIES[i % len(VIDEO_CATEGORIES)]
        # Most videos were published before the analytics window opens;
        # roughly a third publish *during* the window to show fresh ramp-up.
        published_days_ago = random.randint(-10, window_days + 90)
        published_at = now - timedelta(
            days=published_days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59)
        )
        duration = random.choice([180, 300, 420, 600, 900, 1200, 1800, 2400, 3000])
        popularity = max(3.0, random.lognormvariate(3.3, 0.9))
        videos.append(
            {
                "title": _random_title(category),
                "description": f"A {category.lower()} video exploring practical, production-style workflows.",
                "category": category,
                "duration_seconds": duration,
                "thumbnail_url": f"https://picsum.photos/seed/streampulse-{i}/480/270",
                "published_at": published_at,
                "_popularity": popularity,
            }
        )
    return videos


def _lifecycle_factor(age_days: int) -> float:
    if age_days < 0:
        return 0.0
    spike = 6.5 * (2.71828 ** (-age_days / 7.0))
    baseline = 0.4
    return baseline + spike


def _weekday_factor(day: datetime) -> float:
    return 1.15 if day.weekday() < 5 else 0.72


def _random_time_on_day(day_date) -> datetime:
    hour = _weighted_choice(list(range(24)), HOUR_WEIGHTS)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(day_date.year, day_date.month, day_date.day, hour, minute, second, tzinfo=timezone.utc)


def _watch_percent() -> float:
    raw = random.betavariate(2.0, 2.3) * 118
    return round(min(raw, 100.0), 1)


def seed(reset: bool = False) -> None:
    if reset:
        print("Dropping and recreating all tables...")
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    random.seed(settings.seed_random_seed)

    db: Session = SessionLocal()
    try:
        if not reset and db.query(Video).first() is not None:
            print("Videos already present — skipping seed. Use --reset to regenerate.")
            return

        if db.query(User).filter(User.email == DEMO_USER_EMAIL).first() is None:
            db.add(
                User(
                    email=DEMO_USER_EMAIL,
                    hashed_password=hash_password(DEMO_USER_PASSWORD),
                    full_name="Demo Analyst",
                )
            )
            db.commit()
            print(f"Created demo user: {DEMO_USER_EMAIL} / {DEMO_USER_PASSWORD}")

        window_days = settings.seed_days
        n_videos = settings.seed_videos

        print(f"Generating {n_videos} videos over a {window_days}-day analytics window...")
        video_rows = _make_videos(n_videos, window_days)
        popularities = [v.pop("_popularity") for v in video_rows]

        db.execute(insert(Video.__table__), video_rows)
        db.commit()

        video_ids = [row[0] for row in db.query(Video.id).order_by(Video.id).all()]
        published_at_by_id = dict(db.query(Video.id, Video.published_at).all())
        duration_by_id = dict(db.query(Video.id, Video.duration_seconds).all())
        popularity_by_id = dict(zip(video_ids, popularities))

        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(days=window_days - 1)).date()

        view_batch: list[dict] = []
        engagement_batch: list[dict] = []
        total_views = 0
        total_engagements = 0
        BATCH_SIZE = 8000

        def flush():
            nonlocal view_batch, engagement_batch, total_views, total_engagements
            if view_batch:
                db.execute(insert(ViewEvent.__table__), view_batch)
                total_views += len(view_batch)
                view_batch = []
            if engagement_batch:
                db.execute(insert(EngagementEvent.__table__), engagement_batch)
                total_engagements += len(engagement_batch)
                engagement_batch = []
            db.commit()

        day_cursor = window_start
        today = now.date()
        day_index = 0
        while day_cursor <= today:
            for video_id in video_ids:
                published_at = published_at_by_id[video_id]
                duration = duration_by_id[video_id]
                popularity = popularity_by_id[video_id]

                age_days = (day_cursor - published_at.date()).days
                if age_days < 0:
                    continue

                expected = (
                    popularity
                    * _lifecycle_factor(age_days)
                    * _weekday_factor(datetime(day_cursor.year, day_cursor.month, day_cursor.day))
                    * random.uniform(0.75, 1.3)
                )
                daily_views = max(0, min(settings.seed_max_daily_events_per_video, round(random.gauss(expected, expected * 0.25 + 1))))

                for _ in range(daily_views):
                    occurred_at = _random_time_on_day(day_cursor)
                    viewer_id = f"v-{random.getrandbits(48):x}"
                    watch_percent = _watch_percent()
                    watch_seconds = int(duration * (watch_percent / 100))
                    completed = watch_percent >= 95.0
                    device_type = _weighted_choice(list(DEVICE_WEIGHTS.keys()), list(DEVICE_WEIGHTS.values()))
                    country_code = _weighted_choice([c[0] for c in COUNTRIES], COUNTRY_WEIGHTS)
                    referrer = _weighted_choice(list(REFERRER_WEIGHTS.keys()), list(REFERRER_WEIGHTS.values()))

                    view_batch.append(
                        {
                            "video_id": video_id,
                            "viewer_id": viewer_id,
                            "occurred_at": occurred_at,
                            "watch_seconds": watch_seconds,
                            "watch_percent": watch_percent,
                            "completed": completed,
                            "device_type": device_type,
                            "country_code": country_code,
                            "referrer_source": referrer,
                        }
                    )

                    engagement_batch.append(
                        {
                            "video_id": video_id,
                            "viewer_id": viewer_id,
                            "occurred_at": occurred_at,
                            "event_type": EngagementType.play,
                        }
                    )
                    if watch_percent >= 25:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.reach_25,
                            }
                        )
                    if watch_percent >= 50:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.reach_50,
                            }
                        )
                    if watch_percent >= 75:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.reach_75,
                            }
                        )
                    if completed:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.complete,
                            }
                        )

                    engagement_chance = watch_percent / 100.0
                    if random.random() < engagement_chance * 0.16:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.like,
                            }
                        )
                    if random.random() < engagement_chance * 0.035:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.comment,
                            }
                        )
                    if random.random() < engagement_chance * 0.025:
                        engagement_batch.append(
                            {
                                "video_id": video_id,
                                "viewer_id": viewer_id,
                                "occurred_at": occurred_at,
                                "event_type": EngagementType.share,
                            }
                        )

                    if len(view_batch) >= BATCH_SIZE:
                        flush()

            day_index += 1
            if day_index % 15 == 0:
                print(f"  ...processed {day_index}/{window_days} days ({total_views} views so far)")
            day_cursor += timedelta(days=1)

        flush()
        print(f"Done. Inserted {total_views} view events and {total_engagements} engagement events "
              f"across {n_videos} videos.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed StreamPulse demo data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first")
    args = parser.parse_args()
    seed(reset=args.reset)
