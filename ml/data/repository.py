"""データベースから学習データを取得するリポジトリ層。"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

if TYPE_CHECKING:
    from app.models.race import Race, RaceEntry

logger = logging.getLogger(__name__)


class DataRepository:
    """データベースからレースデータを取得し、DataFrameに変換するリポジトリ。"""

    def __init__(self, session: Session) -> None:
        """リポジトリを初期化する。

        Args:
            session: SQLAlchemyセッション
        """
        self._session = session

    def fetch_training_data(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        min_entries: int = 3,
    ) -> pd.DataFrame:
        """学習用データを取得する。

        Args:
            start_date: 取得開始日（Noneの場合は制限なし）
            end_date: 取得終了日（Noneの場合は制限なし）
            min_entries: レースに必要な最小出走馬数

        Returns:
            特徴量とターゲットを含むDataFrame
        """
        from app.models.race import Race, RaceEntry

        statement = (
            select(Race)
            .options(
                selectinload(Race.entries).selectinload(RaceEntry.horse),
                selectinload(Race.entries).selectinload(RaceEntry.jockey),
                selectinload(Race.entries).selectinload(RaceEntry.trainer),
                selectinload(Race.weather),
            )
            .where(Race.race_date.isnot(None))
        )

        if start_date:
            statement = statement.where(Race.race_date >= start_date)
        if end_date:
            statement = statement.where(Race.race_date <= end_date)

        races = list(self._session.scalars(statement).all())

        records: list[dict[str, object]] = []
        for race in races:
            if len(race.entries) < min_entries:
                continue

            for entry in race.entries:
                if entry.final_position is None:
                    continue

                record = self._build_record(race, entry)
                records.append(record)

        if not records:
            logger.warning("No training data found")
            return pd.DataFrame()

        df = pd.DataFrame(records)
        logger.info(f"Fetched {len(df)} records from {len(races)} races")
        return df

    def _build_record(self, race: Race, entry: RaceEntry) -> dict[str, object]:
        """レースとエントリから特徴量レコードを構築する。

        Args:
            race: レース情報
            entry: 出走馬エントリ

        Returns:
            特徴量レコード
        """
        horse = entry.horse
        jockey = entry.jockey
        trainer = entry.trainer
        weather = race.weather

        record: dict[str, object] = {
            # 識別子
            "race_id": race.id,
            "race_entry_id": entry.id,
            "horse_id": entry.horse_id,
            # ターゲット
            "target_win": 1 if entry.final_position == 1 else 0,
            "target_position": entry.final_position,
            # レース特徴量
            "race_date": race.race_date,
            "venue": race.venue,
            "course_type": race.course_type,
            "distance": race.distance,
            "grade": race.grade if race.grade else "",
            "num_entries": len(race.entries),
            # 天候特徴量
            "weather_condition": weather.condition if weather else "",
            "temperature": float(weather.temperature_c) if weather and weather.temperature_c else None,
            "track_condition": weather.track_condition if weather else "",
            # エントリ特徴量
            "horse_number": entry.horse_number if entry.horse_number else -1,
            "post_position": entry.post_position if entry.post_position else -1,
            "odds": float(entry.odds) if entry.odds else None,
            "carried_weight": float(entry.carried_weight) if entry.carried_weight else None,
            # 馬特徴量
            "horse_sex": horse.sex if horse else "",
            "horse_age": (
                (race.race_date - horse.birth_date).days // 365
                if horse and horse.birth_date and race.race_date
                else None
            ),
            # 騎手特徴量
            "jockey_id": jockey.id if jockey else None,
            "jockey_license_area": jockey.license_area if jockey else "",
            # 調教師特徴量
            "trainer_id": trainer.id if trainer else None,
            "trainer_license_area": trainer.license_area if trainer else "",
        }

        return record

    def fetch_race_for_prediction(self, race_id: int) -> pd.DataFrame:
        """予測用のレースデータを取得する。

        Args:
            race_id: レースID

        Returns:
            特徴量を含むDataFrame（ターゲットなし）
        """
        from app.models.race import Race, RaceEntry

        statement = (
            select(Race)
            .options(
                selectinload(Race.entries).selectinload(RaceEntry.horse),
                selectinload(Race.entries).selectinload(RaceEntry.jockey),
                selectinload(Race.entries).selectinload(RaceEntry.trainer),
                selectinload(Race.weather),
            )
            .where(Race.id == race_id)
        )

        race = self._session.scalars(statement).first()
        if race is None:
            raise ValueError(f"Race {race_id} not found")

        records: list[dict[str, object]] = []
        for entry in race.entries:
            record = self._build_record(race, entry)
            records.append(record)

        return pd.DataFrame(records)

