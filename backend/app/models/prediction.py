"""
予測モデル
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Prediction(Base):
    """予測モデル"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    prediction_data = Column(JSON)  # 予測結果データ（馬番ごとの確率など）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    user = relationship("User", back_populates="predictions")
    race = relationship("Race", back_populates="predictions")
    prediction_history = relationship("PredictionHistory", back_populates="prediction", uselist=False)


class PredictionHistory(Base):
    """予測履歴モデル"""
    __tablename__ = "prediction_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    hit_count = Column(Integer, default=0)  # 的中数（3着以内）
    accuracy = Column(Float)  # 的中率
    return_rate = Column(Float)  # 回収率
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    user = relationship("User", back_populates="prediction_histories")
    prediction = relationship("Prediction", back_populates="prediction_history")
    race = relationship("Race", foreign_keys=[race_id])


class RaceResult(Base):
    """レース結果モデル"""
    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, unique=True)
    result_data = Column(JSON)  # 結果データ（着順、タイムなど）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    race = relationship("Race", back_populates="race_result")

