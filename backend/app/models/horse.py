"""競走馬情報を保持する ORM モデル定義。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.race import RaceEntry


class Horse(Base):
    """競走馬のプロフィールを表現するモデル。"""

    __tablename__ = "horses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sire: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dam: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
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
        back_populates="horse",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Horse(id={self.id!r}, name={self.name!r})"


__all__ = ["Horse"]


