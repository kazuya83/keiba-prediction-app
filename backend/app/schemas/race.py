"""レースおよび出走情報のスキーマ定義。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.horse import HorseRead
from app.schemas.jockey import JockeyRead
from app.schemas.trainer import TrainerRead
from app.schemas.weather import WeatherRead


class RaceBase(BaseModel):
    """レース情報の共通スキーマ。"""

    name: str
    race_date: date
    venue: str
    course_type: str
    distance: int
    grade: str | None = None
    start_time: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class RaceEntryBase(BaseModel):
    """出走情報の共通スキーマ。"""

    horse_number: int | None = None
    post_position: int | None = None
    final_position: int | None = None
    odds: Decimal | None = None
    carried_weight: Decimal | None = None
    comment: str | None = None

    model_config = ConfigDict(extra="forbid")


class RaceEntryRead(RaceEntryBase):
    """レース出走情報の読み取りスキーマ。"""

    id: int
    race_id: int
    horse: HorseRead
    jockey: JockeyRead | None = None
    trainer: TrainerRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RaceSummary(RaceBase):
    """一覧表示などで利用するレース概要スキーマ。"""

    id: int
    weather: WeatherRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RaceDetail(RaceSummary):
    """レース詳細表示用スキーマ。"""

    entries: list[RaceEntryRead] = Field(default_factory=list)


class RaceListResponse(BaseModel):
    """レース一覧レスポンスのスキーマ。"""

    items: list[RaceSummary]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)


__all__ = ["RaceBase", "RaceDetail", "RaceEntryBase", "RaceEntryRead", "RaceListResponse", "RaceSummary"]


