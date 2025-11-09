"""参照データを提供する API ルータ。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi_cache.decorator import cache
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.models.horse import Horse
from app.models.jockey import Jockey
from app.models.trainer import Trainer
from app.models.weather import Weather
from app.schemas.horse import HorseRead
from app.schemas.jockey import JockeyRead
from app.schemas.trainer import TrainerRead
from app.schemas.weather import WeatherRead

router = APIRouter(prefix="/reference", tags=["reference"])
settings = get_settings()


def _paginate(statement: Select[tuple], *, limit: int, offset: int) -> Select[tuple]:
    return statement.offset(offset).limit(limit)


def _fetch_list(db: Session, statement: Select[tuple]) -> list:
    return list(db.scalars(statement))


@router.get(
    "/horses",
    response_model=list[HorseRead],
    summary="馬情報の一覧を取得する",
)
@cache(expire=settings.reference_cache_ttl_seconds, namespace="reference:horses")
def list_horses(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(default=100, ge=1, le=500, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
) -> list[HorseRead]:
    statement = _paginate(
        select(Horse).order_by(Horse.name.asc()),
        limit=limit,
        offset=offset,
    )
    return _fetch_list(db, statement)


@router.get(
    "/jockeys",
    response_model=list[JockeyRead],
    summary="騎手情報の一覧を取得する",
)
@cache(expire=settings.reference_cache_ttl_seconds, namespace="reference:jockeys")
def list_jockeys(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(default=100, ge=1, le=500, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
) -> list[JockeyRead]:
    statement = _paginate(
        select(Jockey).order_by(Jockey.name.asc()),
        limit=limit,
        offset=offset,
    )
    return _fetch_list(db, statement)


@router.get(
    "/trainers",
    response_model=list[TrainerRead],
    summary="調教師情報の一覧を取得する",
)
@cache(expire=settings.reference_cache_ttl_seconds, namespace="reference:trainers")
def list_trainers(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(default=100, ge=1, le=500, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
) -> list[TrainerRead]:
    statement = _paginate(
        select(Trainer).order_by(Trainer.name.asc()),
        limit=limit,
        offset=offset,
    )
    return _fetch_list(db, statement)


@router.get(
    "/weathers",
    response_model=list[WeatherRead],
    summary="天候情報の一覧を取得する",
)
@cache(expire=settings.reference_cache_ttl_seconds, namespace="reference:weathers")
def list_weathers(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(default=100, ge=1, le=500, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="取得開始位置"),
) -> list[WeatherRead]:
    statement = _paginate(
        select(Weather).order_by(Weather.created_at.desc()),
        limit=limit,
        offset=offset,
    )
    return _fetch_list(db, statement)


__all__ = ["router"]


