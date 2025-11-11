from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import cast

import pytest

from app.scraping.client import AsyncThrottledClient
from app.scraping.jra import JRARaceScraper
from app.scraping.local_keiba import LocalKeibaRaceScraper
from app.scraping.netkeiba import NetkeibaRaceScraper
from app.schemas.scraping import ScrapingSite

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "scraping"


def _load_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("scraper_cls", "fixture_name", "site", "expected"),
    [
        (
            NetkeibaRaceScraper,
            "netkeiba_race.html",
            ScrapingSite.NETKEIBA,
            {
                "name": "皐月賞(G1)",
                "venue": "中山",
                "distance": 2000,
                "course_type": "芝",
                "entry_count": 2,
            },
        ),
        (
            JRARaceScraper,
            "jra_race.html",
            ScrapingSite.JRA,
            {
                "name": "天皇賞(春)(G1)",
                "venue": "京都",
                "distance": 3200,
                "course_type": "芝",
                "entry_count": 2,
            },
        ),
        (
            LocalKeibaRaceScraper,
            "local_race.html",
            ScrapingSite.LOCAL_KEIBA,
            {
                "name": "東京ダービー(重賞)",
                "venue": "大井",
                "distance": 2000,
                "course_type": "ダート",
                "entry_count": 2,
            },
        ),
    ],
)
def test_scraper_parse_html(scraper_cls, fixture_name, site, expected) -> None:
    dummy_client = cast(AsyncThrottledClient, object())
    scraper = scraper_cls(dummy_client)  # type: ignore[arg-type]
    html = _load_fixture(fixture_name)
    race = scraper.parse_html(race_id="TEST1234", html=html)

    assert race.source == site
    assert race.name == expected["name"]
    assert race.venue == expected["venue"]
    assert race.distance == expected["distance"]
    assert race.course_type == expected["course_type"]
    assert len(race.entries) == expected["entry_count"]
    assert race.source_last_modified is None or isinstance(race.source_last_modified, datetime)
    assert race.entries[0].horse.name != ""


