"""予測履歴および統計計算を扱う CRUD 操作を定義する。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Sequence

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.prediction import Prediction, PredictionResult
from app.models.prediction_history import PredictionHistory
from app.models.race import RaceEntry

ZERO_DECIMAL = Decimal("0")


@dataclass(slots=True)
class PredictionPickInput:
    """予測作成時に利用する順位候補入力値。"""

    rank: int
    race_entry_id: int | None = None
    probability: Decimal | float | int | None = None
    odds: Decimal | float | int | None = None


@dataclass(slots=True)
class PredictionListParams:
    """予測履歴一覧取得のためのフィルタ条件。"""

    user_id: int
    limit: int = 20
    offset: int = 0
    start_at: datetime | None = None
    end_at: datetime | None = None
    race_id: int | None = None
    venue: str | None = None
    result: PredictionResult | None = None


@dataclass(slots=True)
class PredictionStatsData:
    """SQL 集計結果を保持する内部用データ。"""

    total: int
    hit_count: int
    hit_rate: Decimal
    total_stake: Decimal
    total_payout: Decimal
    return_rate: Decimal


@dataclass(slots=True)
class PredictionListResult:
    """一覧取得処理の結果をまとめたデータ。"""

    items: list[Prediction]
    total: int
    params: PredictionListParams
    stats: PredictionStatsData


@dataclass(slots=True)
class PredictionComparisonResult:
    """比較 API 用の結果。"""

    current: Prediction
    history: list[Prediction]


def _to_decimal(value: Decimal | float | int | None, *, default: Decimal | None = None) -> Decimal | None:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _sorted_picks(picks: Iterable[PredictionPickInput]) -> list[PredictionPickInput]:
    return sorted(picks, key=lambda pick: pick.rank)


def _base_query() -> Select[tuple[Prediction]]:
    return (
        select(Prediction)
        .join(Prediction.race)
        .options(
            joinedload(Prediction.race),
            selectinload(Prediction.picks)
            .joinedload(PredictionHistory.race_entry)
            .joinedload(RaceEntry.horse),
        )
        .order_by(Prediction.prediction_at.desc(), Prediction.id.desc())
    )


def _apply_filters(statement: Select[tuple[Prediction]], params: PredictionListParams) -> Select[tuple[Prediction]]:
    statement = statement.where(Prediction.user_id == params.user_id)
    if params.start_at is not None:
        statement = statement.where(Prediction.prediction_at >= params.start_at)
    if params.end_at is not None:
        statement = statement.where(Prediction.prediction_at <= params.end_at)
    if params.race_id is not None:
        statement = statement.where(Prediction.race_id == params.race_id)
    if params.venue is not None:
        statement = statement.where(Prediction.race.has(venue=params.venue))
    if params.result is not None:
        statement = statement.where(Prediction.result == params.result)
    return statement


def create_prediction(
    db: Session,
    *,
    user_id: int,
    race_id: int,
    picks: Sequence[PredictionPickInput] = (),
    prediction_at: datetime | None = None,
    model_version: str | None = None,
    stake_amount: Decimal | float | int | None = None,
    odds: Decimal | float | int | None = None,
    payout: Decimal | float | int | None = None,
    result: PredictionResult = PredictionResult.PENDING,
    memo: str | None = None,
) -> Prediction:
    """予測結果と順位候補を永続化する。"""
    stake_value = _to_decimal(stake_amount, default=Decimal("100.00")) or Decimal("100.00")
    payout_value = _to_decimal(payout, default=ZERO_DECIMAL) or ZERO_DECIMAL
    odds_value = _to_decimal(odds)

    prediction = Prediction(
        user_id=user_id,
        race_id=race_id,
        model_version=model_version,
        prediction_at=prediction_at or datetime.now(timezone.utc),
        stake_amount=stake_value,
        odds=odds_value,
        payout=payout_value,
        result=result,
        memo=memo,
    )

    for pick in _sorted_picks(picks):
        prediction.picks.append(
            PredictionHistory(
                rank=pick.rank,
                race_entry_id=pick.race_entry_id,
                probability=_to_decimal(pick.probability),
                odds=_to_decimal(pick.odds),
            )
        )

    db.add(prediction)
    db.flush()
    db.refresh(prediction)
    return prediction


def list_predictions(db: Session, params: PredictionListParams) -> PredictionListResult:
    """指定した条件で予測履歴を取得し、統計値を併せて返す。"""
    statement = _apply_filters(_base_query(), params)
    limited_statement = statement.offset(params.offset).limit(params.limit)
    items = db.scalars(limited_statement).all()

    count_statement = _apply_filters(
        select(func.count(Prediction.id)),
        params,
    )
    total = int(db.scalar(count_statement) or 0)

    stats_statement = _apply_filters(
        select(
            func.count(Prediction.id),
            func.sum(
                case(
                    (Prediction.result == PredictionResult.HIT, 1),
                    else_=0,
                )
            ),
            func.sum(Prediction.stake_amount),
            func.sum(Prediction.payout),
        ),
        params,
    )
    total_count, hit_count, total_stake, total_payout = db.execute(stats_statement).one()

    total_count = int(total_count or 0)
    hit_count = int(hit_count or 0)
    total_stake_decimal = (total_stake or ZERO_DECIMAL).quantize(Decimal("0.01")) if total_stake else ZERO_DECIMAL
    total_payout_decimal = (total_payout or ZERO_DECIMAL).quantize(Decimal("0.01")) if total_payout else ZERO_DECIMAL

    if total_count == 0:
        hit_rate = ZERO_DECIMAL
    else:
        hit_rate = (Decimal(hit_count) / Decimal(total_count)).quantize(Decimal("0.0001"))

    if total_stake_decimal == ZERO_DECIMAL:
        return_rate = ZERO_DECIMAL
    else:
        return_rate = (total_payout_decimal / total_stake_decimal).quantize(Decimal("0.0001"))

    stats = PredictionStatsData(
        total=total_count,
        hit_count=hit_count,
        hit_rate=hit_rate,
        total_stake=total_stake_decimal,
        total_payout=total_payout_decimal,
        return_rate=return_rate,
    )

    return PredictionListResult(
        items=items,
        total=total,
        params=params,
        stats=stats,
    )


def get_prediction(db: Session, prediction_id: int, *, user_id: int) -> Prediction | None:
    """ユーザー権限付きで予測詳細を取得する。"""
    statement = _apply_filters(
        _base_query().where(Prediction.id == prediction_id),
        PredictionListParams(user_id=user_id),
    )
    return db.scalars(statement).first()


def get_prediction_or_raise(db: Session, prediction_id: int, *, user_id: int) -> Prediction:
    """存在しない場合は ValueError を送出する取得関数。"""
    prediction = get_prediction(db, prediction_id, user_id=user_id)
    if prediction is None:
        raise ValueError("prediction not found")
    return prediction


def get_prediction_comparison(
    db: Session,
    prediction_id: int,
    *,
    user_id: int,
) -> PredictionComparisonResult:
    """同一レースに対する他予測との比較データを取得する。"""
    current = get_prediction_or_raise(db, prediction_id, user_id=user_id)

    history_statement = (
        _apply_filters(
            _base_query(),
            PredictionListParams(
                user_id=user_id,
                race_id=current.race_id,
            ),
        )
        .where(Prediction.id != current.id)
        .limit(10)
    )
    history = db.scalars(history_statement).all()

    return PredictionComparisonResult(current=current, history=history)


__all__ = [
    "PredictionComparisonResult",
    "PredictionListParams",
    "PredictionListResult",
    "PredictionPickInput",
    "PredictionStatsData",
    "create_prediction",
    "get_prediction",
    "get_prediction_comparison",
    "get_prediction_or_raise",
    "list_predictions",
]


