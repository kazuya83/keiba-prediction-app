"""調教師スキーマ定義。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TrainerBase(BaseModel):
    """調教師情報の共通スキーマ。"""

    name: str
    stable_location: str | None = None
    license_area: str | None = None
    birth_date: date | None = None

    model_config = ConfigDict(extra="forbid")


class TrainerRead(TrainerBase):
    """調教師情報の読み取りスキーマ。"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ["TrainerBase", "TrainerRead"]


