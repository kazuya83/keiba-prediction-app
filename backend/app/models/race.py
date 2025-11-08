"""
レースモデル
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class RaceType(str, enum.Enum):
    """レースタイプ"""
    JRA = "jra"  # 中央競馬
    LOCAL = "local"  # 地方競馬


class RaceStatus(str, enum.Enum):
    """レースステータス"""
    SCHEDULED = "scheduled"  # 開催予定
    IN_PROGRESS = "in_progress"  # 開催中
    FINISHED = "finished"  # 終了


class Race(Base):
    """レースモデル"""
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    race_name = Column(String(255), nullable=False)
    race_date = Column(Date, nullable=False)
    race_type = Column(SQLEnum(RaceType), nullable=False)
    venue = Column(String(100))  # 競馬場
    race_number = Column(Integer)  # レース番号
    distance = Column(Integer)  # 距離（メートル）
    surface = Column(String(50))  # 芝・ダート
    track_condition = Column(String(50))  # 馬場状態
    weather = Column(String(50))  # 天候
    status = Column(SQLEnum(RaceStatus), default=RaceStatus.SCHEDULED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーションシップ
    horses = relationship("Horse", back_populates="race", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="race", cascade="all, delete-orphan")
    race_result = relationship("RaceResult", back_populates="race", uselist=False, cascade="all, delete-orphan")
    prediction_histories = relationship("PredictionHistory", foreign_keys="[PredictionHistory.race_id]", backref="race")


class Horse(Base):
    """馬モデル"""
    __tablename__ = "horses"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    horse_name = Column(String(100), nullable=False)
    horse_number = Column(Integer)  # 馬番
    jockey_id = Column(Integer, ForeignKey("jockeys.id"))
    trainer_id = Column(Integer, ForeignKey("trainers.id"))
    weight = Column(Float)  # 斤量
    odds = Column(Float)  # オッズ
    popularity = Column(Integer)  # 人気
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    race = relationship("Race", back_populates="horses")
    jockey = relationship("Jockey", back_populates="horses")
    trainer = relationship("Trainer", back_populates="horses")


class Jockey(Base):
    """騎手モデル"""
    __tablename__ = "jockeys"

    id = Column(Integer, primary_key=True, index=True)
    jockey_name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    horses = relationship("Horse", back_populates="jockey")


class Trainer(Base):
    """調教師モデル"""
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    trainer_name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    horses = relationship("Horse", back_populates="trainer")

