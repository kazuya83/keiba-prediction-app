"""レース参照用の API ルータ。"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.crud.race import SqlAlchemyRaceRepository
from app.schemas.race import RaceDetail, RaceEntryRead, RaceListResponse, RaceSummary

router = APIRouter(prefix="/races", tags=["races"])

settings = get_settings()


@router.get(
    "",
    response_model=RaceListResponse,
    summary="レース一覧を取得する",
)
@cache(expire=settings.race_cache_ttl_seconds, namespace="races:list")
def list_races(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(default=50, ge=1, le=100, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
    race_date: date | None = Query(default=None, description="開催日（YYYY-MM-DD形式）"),
    venue: str | None = Query(
        default=None,
        min_length=1,
        max_length=64,
        description="開催場コード（例: 東京, 京都 など）",
    ),
) -> RaceListResponse:
    """レース一覧をページネーション付きで返す。"""
    repository = SqlAlchemyRaceRepository(db)
    sanitized_venue = venue.strip() if venue is not None else None
    races = repository.list(
        limit=limit,
        offset=offset,
        race_date=race_date,
        venue=sanitized_venue,
    )
    total = repository.count(
        race_date=race_date,
        venue=sanitized_venue,
    )
    return RaceListResponse(items=list(races), total=total, limit=limit, offset=offset)


@router.get(
    "/{race_id}",
    response_model=RaceDetail,
    summary="レース詳細を取得する",
)
@cache(expire=settings.race_cache_ttl_seconds, namespace="races:detail")
def get_race_detail(
    race_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
) -> RaceDetail:
    """レース詳細情報を取得する。"""
    repository = SqlAlchemyRaceRepository(db)
    race = repository.get(race_id)
    if race is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定したレースが見つかりません。",
        )

    entries_sorted = sorted(
        race.entries,
        key=lambda entry: (
            entry.horse_number if entry.horse_number is not None else 999,
            entry.post_position if entry.post_position is not None else 999,
            entry.id,
        ),
    )
    summary = RaceSummary.model_validate(race)
    entry_models = [RaceEntryRead.model_validate(entry) for entry in entries_sorted]
    return RaceDetail(entries=entry_models, **summary.model_dump())


__all__ = ["router"]


