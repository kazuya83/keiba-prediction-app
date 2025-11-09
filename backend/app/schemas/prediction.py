"""予測履歴および統計情報のスキーマ定義。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.prediction import PredictionResult
from app.schemas.race import RaceSummary


class PredictionPickRead(BaseModel):
    """予測に含まれる順位候補のスキーマ。"""

    id: int
    rank: int = Field(ge=1)
    probability: Decimal | None = Field(default=None, ge=0, le=1)
    odds: Decimal | None = Field(default=None, ge=0)
    race_entry_id: int | None = None
    horse_name: str | None = None
    horse_number: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(from_attributes=True)


class PredictionStats(BaseModel):
    """予測履歴に対する統計値。"""

    total: int = Field(ge=0)
    hit_count: int = Field(ge=0)
    hit_rate: Decimal = Field(ge=0)
    total_stake: Decimal = Field(ge=0)
    total_payout: Decimal = Field(ge=0)
    return_rate: Decimal = Field(ge=0)


class PredictionSummary(BaseModel):
    """予測履歴の一覧表示向けスキーマ。"""

    id: int
    race: RaceSummary
    prediction_at: datetime
    result: PredictionResult
    odds: Decimal | None = Field(default=None, ge=0)
    payout: Decimal = Field(ge=0)
    stake_amount: Decimal = Field(ge=0)
    return_rate: Decimal = Field(ge=0)
    picks: list[PredictionPickRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionDetail(PredictionSummary):
    """予測詳細表示向けスキーマ。"""

    model_version: str | None = None
    memo: str | None = None


class PredictionListResponse(BaseModel):
    """予測履歴一覧レスポンス。"""

    items: list[PredictionSummary]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    stats: PredictionStats


class PredictionCompareItem(BaseModel):
    """予測比較の候補スキーマ。"""

    id: int
    prediction_at: datetime
    result: PredictionResult
    odds: Decimal | None = Field(default=None, ge=0)
    payout: Decimal = Field(ge=0)
    stake_amount: Decimal = Field(ge=0)
    return_rate: Decimal = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)


class PredictionCompareResponse(BaseModel):
    """予測比較 API のレスポンス。"""

    current: PredictionDetail
    history: list[PredictionCompareItem] = Field(default_factory=list)


__all__ = [
    "PredictionCompareItem",
    "PredictionCompareResponse",
    "PredictionDetail",
    "PredictionListResponse",
    "PredictionPickRead",
    "PredictionStats",
    "PredictionSummary",
]


