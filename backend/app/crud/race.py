"""レース関連モデルの CRUD 操作を提供するモジュール。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.horse import Horse
from app.models.jockey import Jockey
from app.models.race import Race, RaceEntry
from app.models.trainer import Trainer
from app.models.weather import Weather


class RaceRepository(Protocol):
    """レースデータアクセスの抽象インターフェース。キャッシュ層での差し替えを想定。"""

    def get(self, race_id: int) -> Race | None:
        """レース ID から単一レースを取得する。"""

    def list(
        self,
        *,
        limit: int,
        offset: int,
        race_date: date | None,
        venue: str | None,
    ) -> Sequence[Race]:
        """レース一覧を取得する。"""

    def save(self, race: Race) -> Race:
        """レース情報を永続化する。"""


class SqlAlchemyRaceRepository:
    """SQLAlchemy を用いたレースリポジトリ実装。"""

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self) -> Select[tuple[Race]]:
        return (
            select(Race)
            .options(
                selectinload(Race.weather),
                selectinload(Race.entries)
                .selectinload(RaceEntry.horse),
                selectinload(Race.entries)
                .selectinload(RaceEntry.jockey),
                selectinload(Race.entries)
                .selectinload(RaceEntry.trainer),
            )
            .order_by(Race.race_date.desc(), Race.id.desc())
        )

    def get(self, race_id: int) -> Race | None:
        statement = self._base_query().where(Race.id == race_id)
        return self._db.scalars(statement).first()

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        race_date: date | None = None,
        venue: str | None = None,
    ) -> Sequence[Race]:
        statement = self._base_query()
        if race_date is not None:
            statement = statement.where(Race.race_date == race_date)
        if venue is not None:
            statement = statement.where(Race.venue == venue)
        statement = statement.offset(offset).limit(limit)
        return self._db.scalars(statement).all()

    def save(self, race: Race) -> Race:
        self._db.add(race)
        try:
            self._db.commit()
        except IntegrityError:
            self._db.rollback()
            raise
        self._db.refresh(race)
        return race

    def delete(self, race: Race) -> None:
        self._db.delete(race)
        self._db.commit()


def get_or_create_horse(
    db: Session,
    *,
    name: str,
    sex: str | None = None,
    birth_date: date | None = None,
    sire: str | None = None,
    dam: str | None = None,
    color: str | None = None,
) -> Horse:
    """馬名をキーに Horse を取得し、存在しなければ新規作成する。"""
    statement = select(Horse).where(Horse.name == name)
    horse = db.scalars(statement).first()
    if horse is not None:
        return horse

    horse = Horse(
        name=name,
        sex=sex,
        birth_date=birth_date,
        sire=sire,
        dam=dam,
        color=color,
    )
    db.add(horse)
    db.flush()
    return horse


def get_or_create_jockey(
    db: Session,
    *,
    name: str,
    license_area: str | None = None,
    birth_date: date | None = None,
    debut_year: int | None = None,
) -> Jockey:
    """騎手名をキーに Jockey を取得または新規作成する。"""
    statement = select(Jockey).where(Jockey.name == name)
    jockey = db.scalars(statement).first()
    if jockey is not None:
        return jockey

    jockey = Jockey(
        name=name,
        license_area=license_area,
        birth_date=birth_date,
        debut_year=debut_year,
    )
    db.add(jockey)
    db.flush()
    return jockey


def get_or_create_trainer(
    db: Session,
    *,
    name: str,
    stable_location: str | None = None,
    license_area: str | None = None,
    birth_date: date | None = None,
) -> Trainer:
    """調教師名をキーに Trainer を取得または新規作成する。"""
    statement = select(Trainer).where(Trainer.name == name)
    trainer = db.scalars(statement).first()
    if trainer is not None:
        return trainer

    trainer = Trainer(
        name=name,
        stable_location=stable_location,
        license_area=license_area,
        birth_date=birth_date,
    )
    db.add(trainer)
    db.flush()
    return trainer


def create_weather(
    db: Session,
    *,
    condition: str,
    track_condition: str | None = None,
    temperature_c: float | None = None,
    humidity: float | None = None,
    wind_speed_ms: float | None = None,
) -> Weather:
    """天候情報を新規作成する。"""
    weather = Weather(
        condition=condition,
        track_condition=track_condition,
        temperature_c=temperature_c,
        humidity=humidity,
        wind_speed_ms=wind_speed_ms,
    )
    db.add(weather)
    db.flush()
    return weather


def create_race_entry(
    *,
    race: Race,
    horse: Horse,
    jockey: Jockey | None = None,
    trainer: Trainer | None = None,
    horse_number: int | None = None,
    post_position: int | None = None,
    final_position: int | None = None,
    odds: Decimal | float | None = None,
    carried_weight: Decimal | float | None = None,
    comment: str | None = None,
) -> RaceEntry:
    """エントリーモデルを生成し、関連する Race に追加する。"""
    odds_value: Decimal | None
    if odds is None:
        odds_value = None
    elif isinstance(odds, Decimal):
        odds_value = odds
    else:
        odds_value = Decimal(str(odds))

    carried_weight_value: Decimal | None
    if carried_weight is None:
        carried_weight_value = None
    elif isinstance(carried_weight, Decimal):
        carried_weight_value = carried_weight
    else:
        carried_weight_value = Decimal(str(carried_weight))

    entry = RaceEntry(
        horse=horse,
        jockey=jockey,
        trainer=trainer,
        horse_number=horse_number,
        post_position=post_position,
        final_position=final_position,
        odds=odds_value,
        carried_weight=carried_weight_value,
        comment=comment,
    )
    race.entries.append(entry)
    return entry


__all__ = [
    "RaceRepository",
    "SqlAlchemyRaceRepository",
    "create_race_entry",
    "create_weather",
    "get_or_create_horse",
    "get_or_create_jockey",
    "get_or_create_trainer",
]


