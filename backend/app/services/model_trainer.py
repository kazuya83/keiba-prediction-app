"""モデル再学習ジョブをキューイングするサービスを定義する。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ModelTrainingJobStatus(StrEnum):
    """モデル再学習ジョブの状態を表す列挙。"""

    QUEUED = "queued"


@dataclass(slots=True)
class ModelTrainingJobResult:
    """ジョブ投入後に返す結果データ。"""

    job_id: str
    status: ModelTrainingJobStatus
    queued_at: datetime
    metadata: dict[str, Any]


class ModelTrainer:
    """モデル再学習処理のディスパッチャ。"""

    def __init__(self) -> None:
        self._logger = logger

    def enqueue(
        self,
        *,
        model_id: str | None,
        parameters: dict[str, Any] | None = None,
    ) -> ModelTrainingJobResult:
        """非同期ジョブをキューに投入する。"""
        job_id = uuid4().hex
        queued_at = datetime.now(timezone.utc)
        payload = {
            "model_id": model_id,
            "parameters": parameters or {},
        }
        self._logger.info(
            "Model training job enqueued",
            extra={"job_id": job_id, **payload},
        )

        return ModelTrainingJobResult(
            job_id=job_id,
            status=ModelTrainingJobStatus.QUEUED,
            queued_at=queued_at,
            metadata=payload,
        )


__all__ = ["ModelTrainer", "ModelTrainingJobResult", "ModelTrainingJobStatus"]


