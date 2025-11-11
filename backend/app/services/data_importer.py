"""スクレイピング結果をデータベースへ取り込むサービス。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, Literal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.crud.race import (
    create_race_entry,
    create_weather,
    get_or_create_horse,
    get_or_create_jockey,
    get_or_create_trainer,
)
from app.models.race import Race, RaceEntry
from app.schemas.scraping import ScrapedRace, ScrapedRaceEntry

logger = logging.getLogger(__name__)

ImportStatus = Literal["created", "updated", "skipped"]


@dataclass(slots=True)
class ImportSummary:
    """取り込み処理後のサマリーデータ。"""

    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def register(self, status: ImportStatus) -> None:
        if status == "created":
            self.created += 1
        elif status == "updated":
            self.updated += 1
        elif status == "skipped":
            self.skipped += 1

    def register_failure(self, error: Exception, *, race_id: str) -> None:
        self.failed += 1
        message = f"{race_id}: {error}"
        logger.exception("Failed to import race", extra={"race_id": race_id})
        self.errors.append(message)


class RaceDataImporter:
    """スクレイピング済みレースデータを永続化するサービス。"""

    def __init__(self, db: Session) -> None:
        self._db = db

    def import_races(self, races: Iterable[ScrapedRace]) -> ImportSummary:
        """複数レースを取り込み、サマリを返す。"""
        summary = ImportSummary()

        for race_data in races:
            try:
                status = self._import_race(race_data)
                summary.register(status)
                self._db.commit()
            except Exception as exc:  # pragma: no cover - 想定外も rollback
                self._db.rollback()
                summary.register_failure(exc, race_id=race_data.race_id)

        return summary

    def _import_race(self, race_data: ScrapedRace) -> ImportStatus:
        race = self._find_existing_race(race_data)

        if race is None:
            race = self._create_race(race_data)
            status: ImportStatus = "created"
        else:
            if (
                race_data.source_last_modified
                and race.updated_at
                and race.updated_at >= race_data.source_last_modified
            ):
                logger.info(
                    "Skip race import due to up-to-date record",
                    extra={
                        "race_id": race_data.race_id,
                        "name": race.name,
                        "updated_at": race.updated_at,
                        "source_last_modified": race_data.source_last_modified,
                    },
                )
                return "skipped"
            self._update_race(race, race_data)
            status = "updated"

        self._db.flush()
        self._sync_entries(race, race_data.entries)
        return status

    def _find_existing_race(self, race_data: ScrapedRace) -> Race | None:
        statement = (
            select(Race)
            .options(
                selectinload(Race.entries).selectinload(RaceEntry.horse),
                selectinload(Race.entries).selectinload(RaceEntry.jockey),
                selectinload(Race.entries).selectinload(RaceEntry.trainer),
                selectinload(Race.weather),
            )
            .where(
                Race.name == race_data.name,
                Race.race_date == race_data.race_date,
                Race.venue == race_data.venue,
            )
        )
        return self._db.scalars(statement).first()

    def _create_race(self, race_data: ScrapedRace) -> Race:
        race = Race(
            name=race_data.name,
            race_date=race_data.race_date,
            venue=race_data.venue,
            course_type=race_data.course_type,
            distance=race_data.distance,
            grade=race_data.grade,
            start_time=race_data.start_time,
        )
        self._db.add(race)
        if race_data.weather:
            race.weather = create_weather(
                self._db,
                condition=race_data.weather,
                track_condition=race_data.track_condition,
            )
        return race

    def _update_race(self, race: Race, race_data: ScrapedRace) -> None:
        race.name = race_data.name
        race.course_type = race_data.course_type
        race.distance = race_data.distance
        race.grade = race_data.grade
        race.start_time = race_data.start_time
        race.venue = race_data.venue
        race.race_date = race_data.race_date

        if race_data.weather:
            if race.weather is None:
                race.weather = create_weather(
                    self._db,
                    condition=race_data.weather,
                    track_condition=race_data.track_condition,
                )
            else:
                race.weather.condition = race_data.weather
                race.weather.track_condition = race_data.track_condition
        elif race.weather is not None:
            race.weather.condition = "不明"
            race.weather.track_condition = None

    def _sync_entries(self, race: Race, entries: list[ScrapedRaceEntry]) -> None:
        existing_entries = {
            entry.horse.name if entry.horse else f"entry-{entry.id}": entry
            for entry in race.entries
        }
        processed_horse_names: set[str] = set()

        for entry_data in entries:
            horse = get_or_create_horse(
                self._db,
                name=entry_data.horse.name,
                sex=entry_data.horse.sex,
                sire=entry_data.horse.sire,
                dam=entry_data.horse.dam,
                color=entry_data.horse.color,
            )
            jockey = (
                get_or_create_jockey(self._db, name=entry_data.jockey_name)
                if entry_data.jockey_name
                else None
            )
            trainer = (
                get_or_create_trainer(self._db, name=entry_data.trainer_name)
                if entry_data.trainer_name
                else None
            )

            existing = existing_entries.get(horse.name)
            if existing is None:
                create_race_entry(
                    race=race,
                    horse=horse,
                    jockey=jockey,
                    trainer=trainer,
                    horse_number=entry_data.horse_number,
                    post_position=entry_data.post_position,
                    final_position=entry_data.final_position,
                    odds=entry_data.odds,
                    carried_weight=entry_data.carried_weight,
                    comment=entry_data.comment,
                )
            else:
                existing.horse = horse
                existing.jockey = jockey
                existing.trainer = trainer
                existing.horse_number = entry_data.horse_number
                existing.post_position = entry_data.post_position
                existing.final_position = entry_data.final_position
                existing.odds = entry_data.odds
                existing.carried_weight = entry_data.carried_weight
                existing.comment = entry_data.comment

            processed_horse_names.add(horse.name)

        # 古いエントリーは削除
        for horse_name, entry in existing_entries.items():
            if horse_name not in processed_horse_names:
                try:
                    race.entries.remove(entry)
                    self._db.delete(entry)
                except SQLAlchemyError as exc:  # pragma: no cover - 例外監視用
                    logger.warning(
                        "Failed to remove obsolete entry",
                        extra={"horse_name": horse_name, "race_id": race.id},
                    )
                    raise exc


__all__ = ["ImportSummary", "RaceDataImporter"]


