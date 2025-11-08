# データモデルパッケージ
# すべてのモデルをインポートして、Alembicが認識できるようにする
from app.models.user import User, UserRole
from app.models.race import Race, Horse, Jockey, Trainer, RaceType, RaceStatus
from app.models.prediction import Prediction, PredictionHistory, RaceResult
from app.models.notification import Notification

__all__ = [
    "User",
    "UserRole",
    "Race",
    "Horse",
    "Jockey",
    "Trainer",
    "RaceType",
    "RaceStatus",
    "Prediction",
    "PredictionHistory",
    "RaceResult",
    "Notification",
]
