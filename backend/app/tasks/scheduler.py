"""スケジューラ設定とジョブ管理。"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.tasks.jobs import JobResult, JobStatus, notify_admins, run_data_update_job

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SchedulerConfig:
    """スケジューラ設定を表すデータクラス。"""

    # データ更新ジョブのスケジュール（cron表現）
    data_update_cron: str = "0 3 * * *"  # 毎日3時
    data_update_timezone: str = "Asia/Tokyo"
    # ジョブ実行時の設定
    trigger_model_training: bool = True
    # 通知設定
    notify_on_success: bool = False  # 成功時も通知するか
    notify_on_partial: bool = True  # 部分成功時も通知するか
    notify_on_failure: bool = True  # 失敗時も通知するか

    @classmethod
    def from_env(cls) -> SchedulerConfig:
        """環境変数から設定を読み込む。"""
        settings = get_settings()
        return cls(
            data_update_cron=settings.data_update_cron,
            data_update_timezone=settings.data_update_timezone,
            trigger_model_training=settings.trigger_model_training,
            notify_on_success=settings.notify_on_success,
            notify_on_partial=settings.notify_on_partial,
            notify_on_failure=settings.notify_on_failure,
        )


class JobLock:
    """ジョブの同時実行を防ぐためのロック（簡易実装）。"""

    def __init__(self) -> None:
        self._locks: dict[str, bool] = {}

    def acquire(self, job_id: str) -> bool:
        """ロックを取得する。既にロックされている場合はFalseを返す。"""
        if self._locks.get(job_id, False):
            return False
        self._locks[job_id] = True
        return True

    def release(self, job_id: str) -> None:
        """ロックを解放する。"""
        self._locks[job_id] = False


_job_lock = JobLock()


async def _execute_data_update_job(config: SchedulerConfig) -> None:
    """データ更新ジョブを実行する（スケジューラ用ラッパー）。"""
    job_id = "data_update"
    if not _job_lock.acquire(job_id):
        logger.warning("Data update job is already running, skipping")
        return

    try:
        logger.info("Executing scheduled data update job")
        result = await run_data_update_job(trigger_model_training=config.trigger_model_training)

        # 通知を送信
        should_notify = (
            (result.status == JobStatus.SUCCESS and config.notify_on_success)
            or (result.status == JobStatus.PARTIAL and config.notify_on_partial)
            or (result.status == JobStatus.FAILED and config.notify_on_failure)
        )

        if should_notify:
            db = SessionLocal()
            try:
                notify_admins(db, result, job_name="データ更新ジョブ")
            except Exception as exc:
                logger.exception("Failed to send notification", exc_info=exc)
            finally:
                db.close()

        # ログ出力
        if result.status == JobStatus.SUCCESS:
            logger.info(
                "Data update job completed successfully",
                extra={
                    "duration_seconds": result.duration_seconds,
                    **result.metadata,
                },
            )
        elif result.status == JobStatus.PARTIAL:
            logger.warning(
                "Data update job completed with partial success",
                extra={
                    "duration_seconds": result.duration_seconds,
                    **result.metadata,
                },
            )
        else:
            logger.error(
                "Data update job failed",
                extra={
                    "duration_seconds": result.duration_seconds,
                    "error": str(result.error) if result.error else None,
                    **result.metadata,
                },
                exc_info=result.error,
            )
    finally:
        _job_lock.release(job_id)


def setup_scheduler(config: SchedulerConfig | None = None) -> AsyncIOScheduler:
    """スケジューラを設定して返す。"""
    if config is None:
        config = SchedulerConfig.from_env()

    jobstores = {"default": MemoryJobStore()}
    executors = {"default": AsyncIOExecutor()}
    job_defaults = {
        "coalesce": True,  # 複数のジョブが遅延している場合、1つにまとめる
        "max_instances": 1,  # 同時実行は1つのみ
        "misfire_grace_time": 3600,  # 1時間以内の遅延は許容
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=config.data_update_timezone,
    )

    # データ更新ジョブを登録
    try:
        # cron表現をパース（例: "0 3 * * *" -> hour=3, minute=0）
        cron_parts = config.data_update_cron.split()
        if len(cron_parts) != 5:
            raise ValueError(f"Invalid cron expression: {config.data_update_cron}")

        minute_str, hour_str, day_str, month_str, day_of_week_str = cron_parts

        def parse_cron_field(value: str) -> int | str | None:
            """cronフィールドをパースする。"""
            if value == "*":
                return None
            try:
                return int(value)
            except ValueError:
                return value  # 範囲表現などはそのまま返す

        trigger = CronTrigger(
            minute=parse_cron_field(minute_str),
            hour=parse_cron_field(hour_str),
            day=parse_cron_field(day_str),
            month=parse_cron_field(month_str),
            day_of_week=parse_cron_field(day_of_week_str),
            timezone=config.data_update_timezone,
        )
        scheduler.add_job(
            _execute_data_update_job,
            trigger=trigger,
            id="data_update",
            name="データ更新ジョブ",
            args=(config,),
            replace_existing=True,
        )
        logger.info(
            "Scheduled data update job",
            extra={
                "cron": config.data_update_cron,
                "timezone": config.data_update_timezone,
            },
        )
    except Exception as exc:
        logger.exception("Failed to schedule data update job", exc_info=exc)
        raise

    return scheduler


__all__ = ["SchedulerConfig", "setup_scheduler"]

