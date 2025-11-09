"""予測履歴および統計を提供する API ルータ。"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.crud import prediction as prediction_crud
from app.models.prediction import PredictionResult
from app.models.user import User
from app.schemas.prediction import (
    PredictionCompareResponse,
    PredictionDetail,
    PredictionListResponse,
    PredictionStats,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get(
    "",
    response_model=PredictionListResponse,
    summary="予測履歴の一覧を取得する",
    description="ログインユーザーの予測履歴をページネーション付きで取得します。",
)
def list_user_predictions(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    start_at: datetime | None = Query(
        default=None,
        description="取得開始日時 (ISO8601)。未指定の場合は制限なし。",
    ),
    end_at: datetime | None = Query(
        default=None,
        description="取得終了日時 (ISO8601)。未指定の場合は制限なし。",
    ),
    race_id: int | None = Query(
        default=None,
        ge=1,
        description="特定レース ID の履歴に絞り込む。",
    ),
    venue: str | None = Query(
        default=None,
        min_length=1,
        description="開催場名でフィルタリングする。",
    ),
    result: PredictionResult | None = Query(
        default=None,
        description="的中状況でフィルタリングする。",
    ),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> PredictionListResponse:
    params = prediction_crud.PredictionListParams(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        start_at=start_at,
        end_at=end_at,
        race_id=race_id,
        venue=venue,
        result=result,
    )
    result_set = prediction_crud.list_predictions(db, params)
    stats = result_set.stats

    return PredictionListResponse(
        items=result_set.items,
        total=result_set.total,
        limit=limit,
        offset=offset,
        stats=PredictionStats(
            total=stats.total,
            hit_count=stats.hit_count,
            hit_rate=stats.hit_rate,
            total_stake=stats.total_stake,
            total_payout=stats.total_payout,
            return_rate=stats.return_rate,
        ),
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionDetail,
    summary="予測履歴の詳細を取得する",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "指定された予測が見つからない場合に返されます。",
        }
    },
)
def read_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> PredictionDetail:
    prediction = prediction_crud.get_prediction(db, prediction_id, user_id=current_user.id)
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="予測履歴が見つかりません。",
        )
    return prediction


@router.get(
    "/{prediction_id}/compare",
    response_model=PredictionCompareResponse,
    summary="同一レースの予測を比較する",
    description="指定した予測と同レースで過去に実施した予測を比較用に返します。",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "指定された予測が見つからない場合に返されます。",
        }
    },
)
def compare_predictions(
    prediction_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> PredictionCompareResponse:
    try:
        comparison = prediction_crud.get_prediction_comparison(
            db,
            prediction_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="予測履歴が見つかりません。",
        ) from exc

    return PredictionCompareResponse(
        current=comparison.current,
        history=comparison.history,
    )


__all__ = ["router"]


