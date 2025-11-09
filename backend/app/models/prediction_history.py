"""予測履歴の詳細（個々の順位候補）を保持する ORM モデル。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.prediction import Prediction
    from app.models.race import RaceEntry


class PredictionHistory(Base):
    """予測に含まれる順位付け情報を保持するモデル。"""

    __tablename__ = "prediction_histories"
    __table_args__ = (
        UniqueConstraint(
            "prediction_id",
            "rank",
            name="uq_prediction_histories_prediction_rank",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    race_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("race_entries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
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

    prediction: Mapped["Prediction"] = relationship(
        "Prediction",
        back_populates="picks",
    )
    race_entry: Mapped["RaceEntry | None"] = relationship(
        "RaceEntry",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"PredictionHistory(id={self.id!r}, prediction_id={self.prediction_id!r}, "
            f"rank={self.rank!r})"
        )

    @property
    def horse_name(self) -> str | None:
        """紐づく馬名を返す。"""
        if self.race_entry and self.race_entry.horse:
            return self.race_entry.horse.name
        return None

    @property
    def horse_number(self) -> int | None:
        """紐づく馬番を返す。"""
        if self.race_entry:
            return self.race_entry.horse_number
        return None


__all__ = ["PredictionHistory"]


