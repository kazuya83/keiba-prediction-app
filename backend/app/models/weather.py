"""レース開催時の気象条件を保持する ORM モデル定義。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.race import Race


class Weather(Base):
    """レース時の天候や馬場状態などの情報を表すモデル。"""

    __tablename__ = "weathers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    condition: Mapped[str] = mapped_column(String(64), nullable=False)
    track_condition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    races: Mapped[list["Race"]] = relationship(
        "Race",
        back_populates="weather",
    )

    def __repr__(self) -> str:
        return f"Weather(id={self.id!r}, condition={self.condition!r}, track_condition={self.track_condition!r})"


__all__ = ["Weather"]


