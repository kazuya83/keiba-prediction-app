"""レース参照 API のテスト。"""

from __future__ import annotations

from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.race import (
    SqlAlchemyRaceRepository,
    create_race_entry,
    create_weather,
    get_or_create_horse,
    get_or_create_jockey,
    get_or_create_trainer,
)
from app.models.race import Race


def _build_race(
    db_session: Session,
    *,
    race_date: date,
    venue: str,
    name: str,
) -> Race:
    """テスト用に Race モデルを作成する。"""
    weather = create_weather(
        db_session,
        condition="晴",
        track_condition="良",
        temperature_c=20.0,
    )
    return Race(
        name=name,
        race_date=race_date,
        venue=venue,
        course_type="芝",
        distance=2000,
        grade="G1",
        weather=weather,
        start_time=datetime.combine(race_date, datetime.min.time()).replace(hour=15, minute=0),
    )


def test_list_races_returns_filtered_results(
    test_client: TestClient,
    db_session: Session,
) -> None:
    repository = SqlAlchemyRaceRepository(db_session)
    tokyo_race = _build_race(
        db_session,
        race_date=date(2025, 5, 3),
        venue="東京",
        name="東京スプリングステークス",
    )
    kyoto_race = _build_race(
        db_session,
        race_date=date(2025, 6, 1),
        venue="京都",
        name="京都サマーカップ",
    )
    repository.save(tokyo_race)
    repository.save(kyoto_race)

    response = test_client.get(
        "/api/races",
        params={"race_date": "2025-05-03", "venue": "東京"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["name"] == "東京スプリングステークス"


def test_get_race_detail_includes_related_entities(
    test_client: TestClient,
    db_session: Session,
) -> None:
    repository = SqlAlchemyRaceRepository(db_session)
    race = _build_race(
        db_session,
        race_date=date(2025, 7, 20),
        venue="阪神",
        name="阪神チャレンジトロフィー",
    )

    horse = get_or_create_horse(db_session, name="シャイニングスター", sex="牡")
    jockey = get_or_create_jockey(db_session, name="山田 太郎", license_area="JRA")
    trainer = get_or_create_trainer(db_session, name="佐藤 誠", stable_location="栗東")

    create_race_entry(
        race=race,
        horse=horse,
        jockey=jockey,
        trainer=trainer,
        horse_number=5,
        post_position=6,
        final_position=1,
        odds=4.2,
        carried_weight=57.0,
    )

    saved = repository.save(race)

    response = test_client.get(f"/api/races/{saved.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == saved.id
    assert payload["weather"]["condition"] == "晴"
    assert len(payload["entries"]) == 1
    entry = payload["entries"][0]
    assert entry["horse"]["name"] == "シャイニングスター"
    assert entry["jockey"]["name"] == "山田 太郎"
    assert entry["trainer"]["name"] == "佐藤 誠"
    assert entry["horse_number"] == 5


def test_get_race_detail_not_found_returns_404(
    test_client: TestClient,
) -> None:
    response = test_client.get("/api/races/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "指定したレースが見つかりません。"




