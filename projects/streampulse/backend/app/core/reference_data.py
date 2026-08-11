"""Static reference data shared between the seed script and the API layer."""

COUNTRIES: list[tuple[str, str]] = [
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("DE", "Germany"),
    ("SE", "Sweden"),
    ("FR", "France"),
    ("CA", "Canada"),
    ("BR", "Brazil"),
    ("IN", "India"),
    ("AU", "Australia"),
    ("JP", "Japan"),
    ("NL", "Netherlands"),
    ("ES", "Spain"),
    ("MX", "Mexico"),
    ("NG", "Nigeria"),
    ("KR", "South Korea"),
]

COUNTRY_NAME_BY_CODE: dict[str, str] = dict(COUNTRIES)

REFERRER_SOURCES: list[str] = [
    "search",
    "social",
    "direct",
    "email",
    "embed",
    "recommendation",
]

VIDEO_CATEGORIES: list[str] = [
    "Product Updates",
    "Tutorials",
    "Customer Stories",
    "Webinars",
    "Behind the Scenes",
    "Engineering Deep Dives",
    "Highlights",
]

FUNNEL_STAGES: list[tuple[str, str]] = [
    ("play", "Played"),
    ("reach_25", "Reached 25%"),
    ("reach_50", "Reached 50%"),
    ("reach_75", "Reached 75%"),
    ("complete", "Completed"),
]
