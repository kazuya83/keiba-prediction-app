"""レース関連 CRUD のテスト。"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.race import (
    SqlAlchemyRaceRepository,
    create_race_entry,
    create_weather,
    get_or_create_horse,
    get_or_create_jockey,
    get_or_create_trainer,
)
from app.models.race import Race, RaceEntry


def _create_sample_race(session: Session, *, race_date: date, venue: str, name: str) -> Race:
    weather = create_weather(
        session,
        condition="晴",
        track_condition="良",
        temperature_c=20.0,
    )
    race = Race(
        name=name,
        race_date=race_date,
        venue=venue,
        course_type="芝",
        distance=2000,
        grade="G1",
        weather=weather,
        start_time=datetime.combine(race_date, datetime.min.time()).replace(hour=15, minute=30),
    )
    return race


def test_create_and_get_race(db_session: Session) -> None:
    repository = SqlAlchemyRaceRepository(db_session)

    race = _create_sample_race(
        db_session,
        race_date=date(2025, 4, 27),
        venue="東京",
        name="東京スプリングカップ",
    )

    horse = get_or_create_horse(db_session, name="フレッシュスター", sex="牡")
    jockey = get_or_create_jockey(db_session, name="山田 太郎", license_area="JRA")
    trainer = get_or_create_trainer(db_session, name="中村 誠", stable_location="美浦")

    create_race_entry(
        race=race,
        horse=horse,
        jockey=jockey,
        trainer=trainer,
        horse_number=5,
        post_position=6,
        final_position=2,
        odds=6.4,
        carried_weight=57.0,
        comment="好位追走から伸びる",
    )

    saved_race = repository.save(race)

    fetched_race = repository.get(saved_race.id)
    assert fetched_race is not None
    assert fetched_race.weather is not None
    assert fetched_race.weather.condition == "晴"
    assert len(fetched_race.entries) == 1
    assert fetched_race.entries[0].horse.name == "フレッシュスター"
    assert fetched_race.entries[0].jockey is not None
    assert fetched_race.entries[0].trainer is not None


def test_list_races_with_filters(db_session: Session) -> None:
    repository = SqlAlchemyRaceRepository(db_session)

    race_tokyo = _create_sample_race(
        db_session,
        race_date=date(2025, 5, 18),
        venue="東京",
        name="東京優駿",
    )
    race_kyoto = _create_sample_race(
        db_session,
        race_date=date(2025, 5, 25),
        venue="京都",
        name="京都記念",
    )

    repository.save(race_tokyo)
    repository.save(race_kyoto)

    races_tokyo = repository.list(race_date=date(2025, 5, 18), venue="東京")
    assert len(races_tokyo) == 1
    assert races_tokyo[0].name == "東京優駿"

    races_all = repository.list()
    assert len(races_all) >= 2


def test_race_entry_uniqueness_constraint(db_session: Session) -> None:
    repository = SqlAlchemyRaceRepository(db_session)
    race = _create_sample_race(
        db_session,
        race_date=date(2025, 6, 1),
        venue="阪神",
        name="阪神チャレンジカップ",
    )
    horse = get_or_create_horse(db_session, name="ダブルアロー")

    create_race_entry(race=race, horse=horse, horse_number=1)
    repository.save(race)

    duplicate_entry = RaceEntry(
        race=race,
        horse=horse,
    )
    db_session.add(duplicate_entry)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


