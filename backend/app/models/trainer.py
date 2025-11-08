"""調教師情報を保持する ORM モデル定義。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.race import RaceEntry


class Trainer(Base):
    """調教師のプロフィール情報を表現するモデル。"""

    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    stable_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_area: Mapped[str | None] = mapped_column(String(64), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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

    race_entries: Mapped[list["RaceEntry"]] = relationship(
        "RaceEntry",
        back_populates="trainer",
    )

    def __repr__(self) -> str:
        return f"Trainer(id={self.id!r}, name={self.name!r})"


__all__ = ["Trainer"]


