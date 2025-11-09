"""予測結果を保持する ORM モデル定義。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.prediction_history import PredictionHistory
    from app.models.race import Race
    from app.models.user import User


class PredictionResult(StrEnum):
    """予測結果の状態を表す列挙型。"""

    PENDING = "pending"
    HIT = "hit"
    MISS = "miss"


class Prediction(Base):
    """ユーザーが実施した予測結果のメタデータを保持するモデル。"""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stake_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("100.00"),
        server_default=text("100.00"),
    )
    odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    payout: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    result: Mapped[PredictionResult] = mapped_column(
        Enum(PredictionResult, name="prediction_result"),
        nullable=False,
        default=PredictionResult.PENDING,
        server_default=PredictionResult.PENDING.value,
    )
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    prediction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
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

    user: Mapped["User"] = relationship(
        "User",
        back_populates="predictions",
    )
    race: Mapped["Race"] = relationship(
        "Race",
        back_populates="predictions",
    )
    picks: Mapped[list["PredictionHistory"]] = relationship(
        "PredictionHistory",
        back_populates="prediction",
        cascade="all, delete-orphan",
        order_by="PredictionHistory.rank",
    )

    def __repr__(self) -> str:
        return (
            f"Prediction(id={self.id!r}, user_id={self.user_id!r}, "
            f"race_id={self.race_id!r}, result={self.result!r})"
        )

    @property
    def return_rate(self) -> Decimal:
        """投資額に対する回収率を計算して返す。"""
        if self.stake_amount == 0:
            return Decimal("0")
        return (self.payout or Decimal("0")) / self.stake_amount


__all__ = ["Prediction", "PredictionResult"]


