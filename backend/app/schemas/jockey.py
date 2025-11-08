"""騎手スキーマ定義。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class JockeyBase(BaseModel):
    """騎手情報の共通スキーマ。"""

    name: str
    license_area: str | None = None
    birth_date: date | None = None
    debut_year: int | None = None

    model_config = ConfigDict(extra="forbid")


class JockeyRead(JockeyBase):
    """騎手情報の読み取りスキーマ。"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ["JockeyBase", "JockeyRead"]


