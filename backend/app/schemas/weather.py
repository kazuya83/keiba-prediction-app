"""天候スキーマ定義。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WeatherBase(BaseModel):
    """天候情報の共通スキーマ。"""

    condition: str
    track_condition: str | None = None
    temperature_c: float | None = None
    humidity: float | None = None
    wind_speed_ms: float | None = None
    recorded_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class WeatherRead(WeatherBase):
    """天候情報の読み取りスキーマ。"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = ["WeatherBase", "WeatherRead"]


