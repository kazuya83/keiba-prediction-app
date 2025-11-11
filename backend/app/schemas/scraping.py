"""スクレイピングで取得したレースデータの正規化スキーマ定義。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScrapingSite(StrEnum):
    """スクレイピング対象サイトを表す列挙型。"""

    NETKEIBA = "netkeiba"
    JRA = "jra"
    LOCAL_KEIBA = "local_keiba"


class ScrapedHorse(BaseModel):
    """出走馬情報のスキーマ。"""

    name: str = Field(min_length=1)
    sex: str | None = None
    age: int | None = Field(default=None, ge=0, le=50)
    sire: str | None = None
    dam: str | None = None
    color: str | None = None


class ScrapedRaceEntry(BaseModel):
    """レースエントリ情報のスキーマ。"""

    horse: ScrapedHorse
    jockey_name: str | None = None
    trainer_name: str | None = None
    horse_number: int | None = Field(default=None, ge=0)
    post_position: int | None = Field(default=None, ge=0)
    final_position: int | None = Field(default=None, ge=0)
    odds: Decimal | None = Field(default=None, ge=0)
    carried_weight: float | None = Field(default=None, ge=0)
    comment: str | None = None

    @field_validator("carried_weight", mode="before")
    @classmethod
    def _parse_carried_weight(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("carried_weight は数値である必要があります。") from exc

    @field_validator("odds", mode="before")
    @classmethod
    def _parse_odds(cls, value: object) -> Decimal | None:
        if value is None or value == "":
            return None
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (ValueError, TypeError) as exc:
            raise ValueError("odds は数値である必要があります。") from exc


class ScrapedRace(BaseModel):
    """スクレイピング済みレースの正規化データ。"""

    source: ScrapingSite
    race_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    course_type: str = Field(min_length=1)
    distance: int = Field(ge=0)
    grade: str | None = None
    race_date: date
    start_time: datetime | None = None
    weather: str | None = None
    track_condition: str | None = None
    source_last_modified: datetime | None = None
    entries: list[ScrapedRaceEntry]
    raw: dict[str, Any] | None = None


__all__ = [
    "ScrapedHorse",
    "ScrapedRace",
    "ScrapedRaceEntry",
    "ScrapingSite",
]


