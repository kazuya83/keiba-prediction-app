from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import cast

from sqlalchemy import select

from app.models.race import Race
from app.scraping.client import AsyncThrottledClient
from app.scraping.netkeiba import NetkeibaRaceScraper
from app.services.data_importer import RaceDataImporter

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "scraping"


def _load_html(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def _scraped_race():
    dummy_client = cast(AsyncThrottledClient, object())
    scraper = NetkeibaRaceScraper(dummy_client)  # type: ignore[arg-type]
    html = _load_html("netkeiba_race.html")
    return scraper.parse_html(race_id="202404140411", html=html)


def test_data_importer_creates_and_updates_race(db_session) -> None:
    importer = RaceDataImporter(db_session)
    race_data = _scraped_race()

    summary = importer.import_races([race_data])
    assert summary.created == 1
    assert summary.updated == 0
    assert summary.skipped == 0
    assert summary.failed == 0

    race = db_session.scalars(select(Race)).first()
    assert race is not None
    assert race.name == race_data.name
    assert len(race.entries) == len(race_data.entries)

    updated_race_data = race_data.model_copy(deep=True)
    updated_race_data.entries = updated_race_data.entries[:1]
    updated_race_data.entries[0].comment = "更新コメント"
    if updated_race_data.source_last_modified is not None:
        updated_race_data.source_last_modified = updated_race_data.source_last_modified + timedelta(
            minutes=10
        )

    summary2 = importer.import_races([updated_race_data])
    assert summary2.created == 0
    assert summary2.updated == 1
    assert summary2.skipped == 0
    assert summary2.failed == 0

    db_session.expire_all()
    race = db_session.scalars(select(Race)).first()
    assert race is not None
    assert len(race.entries) == 1
    assert race.entries[0].comment == "更新コメント"

    stale_race_data = updated_race_data.model_copy(deep=True)
    if race.updated_at is not None:
        stale_race_data.source_last_modified = race.updated_at - timedelta(minutes=1)

    summary3 = importer.import_races([stale_race_data])
    assert summary3.skipped == 1
    assert summary3.created == 0
    assert summary3.updated == 0
    assert summary3.failed == 0


