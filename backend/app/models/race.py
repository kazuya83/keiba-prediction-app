"""レース情報および出走馬エントリを表現する ORM モデル定義。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.horse import Horse
    from app.models.jockey import Jockey
    from app.models.notification import Notification
    from app.models.prediction import Prediction
    from app.models.trainer import Trainer
    from app.models.weather import Weather


class Race(Base):
    """競馬レースの基本情報を保持するモデル。"""

    __tablename__ = "races"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    race_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    venue: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    course_type: Mapped[str] = mapped_column(String(32), nullable=False)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    weather_id: Mapped[int | None] = mapped_column(
        ForeignKey("weathers.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    weather: Mapped["Weather | None"] = relationship(
        "Weather",
        back_populates="races",
    )
    entries: Mapped[list["RaceEntry"]] = relationship(
        "RaceEntry",
        back_populates="race",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction",
        back_populates="race",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="race",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Race(id={self.id!r}, name={self.name!r}, race_date={self.race_date!r})"


class RaceEntry(Base):
    """レースに出走する馬・騎手・調教師の組み合わせを管理するモデル。"""

    __tablename__ = "race_entries"
    __table_args__ = (
        UniqueConstraint("race_id", "horse_id", name="uq_race_entries_race_horse"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    horse_id: Mapped[int] = mapped_column(
        ForeignKey("horses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    jockey_id: Mapped[int | None] = mapped_column(
        ForeignKey("jockeys.id", ondelete="SET NULL"),
        nullable=True,
    )
    trainer_id: Mapped[int | None] = mapped_column(
        ForeignKey("trainers.id", ondelete="SET NULL"),
        nullable=True,
    )
    horse_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    post_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    carried_weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
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

    race: Mapped["Race"] = relationship(
        "Race",
        back_populates="entries",
    )
    horse: Mapped["Horse"] = relationship(
        "Horse",
        back_populates="race_entries",
    )
    jockey: Mapped["Jockey | None"] = relationship(
        "Jockey",
        back_populates="race_entries",
    )
    trainer: Mapped["Trainer | None"] = relationship(
        "Trainer",
        back_populates="race_entries",
    )

    def __repr__(self) -> str:
        return f"RaceEntry(id={self.id!r}, race_id={self.race_id!r}, horse_id={self.horse_id!r})"


__all__ = ["Race", "RaceEntry"]


