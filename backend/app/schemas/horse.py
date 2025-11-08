"""競走馬スキーマ定義。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class HorseBase(BaseModel):
    """競走馬情報の共通スキーマ。"""

    name: str
    sex: str | None = None
    birth_date: date | None = None
    sire: str | None = None
    dam: str | None = None
    color: str | None = None

    model_config = ConfigDict(extra="forbid")


class HorseRead(HorseBase):
    """競走馬情報を読み取り用に整形したスキーマ。"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ["HorseBase", "HorseRead"]


