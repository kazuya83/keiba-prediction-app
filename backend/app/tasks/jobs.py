"""データ更新ジョブの実装。"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud import user as user_crud
from app.db.session import SessionLocal
from app.models.notification import NotificationCategory
from app.schemas.scraping import ScrapingSite
from app.scraping import (
    AsyncThrottledClient,
    JRARaceScraper,
    LocalKeibaRaceScraper,
    NetkeibaRaceScraper,
    get_policy,
)
from app.services import ModelTrainer, NotificationDispatcher, RaceDataImporter

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY = {
    ScrapingSite.NETKEIBA: NetkeibaRaceScraper,
    ScrapingSite.JRA: JRARaceScraper,
    ScrapingSite.LOCAL_KEIBA: LocalKeibaRaceScraper,
}


class JobStatus(StrEnum):
    """ジョブの実行状態を表す列挙型。"""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass(slots=True)
class JobResult:
    """ジョブ実行結果を表すデータクラス。"""

    status: JobStatus
    message: str
    metadata: dict[str, Any]
    started_at: datetime
    completed_at: datetime
    error: Exception | None = None

    @property
    def duration_seconds(self) -> float:
        """ジョブ実行時間（秒）を返す。"""
        delta = self.completed_at - self.started_at
        return delta.total_seconds()


class DataUpdateJob:
    """データ更新ジョブを実行するクラス。"""

    def __init__(
        self,
        db: Session | None = None,
        *,
        sites: list[ScrapingSite] | None = None,
        race_ids: list[str] | None = None,
        trigger_model_training: bool = True,
    ) -> None:
        """データ更新ジョブを初期化する。

        Args:
            db: データベースセッション。Noneの場合は新規作成。
            sites: スクレイピング対象サイト。Noneの場合は全サイト。
            race_ids: スクレイピング対象のレースID。Noneの場合は自動取得。
            trigger_model_training: データ更新後にモデル再学習をトリガーするか。
        """
        self._db = db
        self._sites = sites or [ScrapingSite.NETKEIBA, ScrapingSite.JRA]
        self._race_ids = race_ids
        self._trigger_model_training = trigger_model_training

    async def run(self) -> JobResult:
        """データ更新ジョブを実行する。"""
        started_at = datetime.now(timezone.utc)
        db = self._db or SessionLocal()
        try:
            logger.info(
                "Starting data update job",
                extra={
                    "sites": [site.value for site in self._sites],
                    "race_ids": self._race_ids,
                },
            )

            # スクレイピング実行
            scraped_races = await self._scrape_races()

            # DB更新
            importer = RaceDataImporter(db)
            summary = importer.import_races(scraped_races)
            db.commit()

            logger.info(
                "Data import completed",
                extra={
                    "created": summary.created,
                    "updated": summary.updated,
                    "skipped": summary.skipped,
                    "failed": summary.failed,
                },
            )

            # モデル再学習をトリガー
            training_job_id: str | None = None
            if self._trigger_model_training and (summary.created > 0 or summary.updated > 0):
                trainer = ModelTrainer()
                training_result = trainer.enqueue(model_id=None, parameters=None)
                training_job_id = training_result.job_id
                logger.info(
                    "Model training job enqueued",
                    extra={"job_id": training_job_id},
                )

            # ジョブ結果を判定
            if summary.failed > 0:
                status = JobStatus.PARTIAL
                message = (
                    f"データ更新が部分的に完了しました。"
                    f"作成: {summary.created}, 更新: {summary.updated}, "
                    f"スキップ: {summary.skipped}, 失敗: {summary.failed}"
                )
            else:
                status = JobStatus.SUCCESS
                message = (
                    f"データ更新が正常に完了しました。"
                    f"作成: {summary.created}, 更新: {summary.updated}, "
                    f"スキップ: {summary.skipped}"
                )

            completed_at = datetime.now(timezone.utc)
            return JobResult(
                status=status,
                message=message,
                metadata={
                    "created": summary.created,
                    "updated": summary.updated,
                    "skipped": summary.skipped,
                    "failed": summary.failed,
                    "errors": summary.errors,
                    "training_job_id": training_job_id,
                },
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as exc:
            logger.exception("Data update job failed", exc_info=exc)
            completed_at = datetime.now(timezone.utc)
            return JobResult(
                status=JobStatus.FAILED,
                message=f"データ更新ジョブが失敗しました: {exc}",
                metadata={},
                started_at=started_at,
                completed_at=completed_at,
                error=exc,
            )
        finally:
            if self._db is None:
                db.close()

    async def _scrape_races(self) -> list:
        """レースデータをスクレイピングする。"""
        from app.schemas.scraping import ScrapedRace

        all_races: list[ScrapedRace] = []

        for site in self._sites:
            policy = get_policy(site.value)
            client = AsyncThrottledClient(policy)
            scraper_class = SCRAPER_REGISTRY[site]
            scraper = scraper_class(client)

            try:
                # レースIDが指定されていない場合は、最新のレースを取得
                # 現時点では、race_idsが指定されている場合のみ対応
                if self._race_ids:
                    for race_id in self._race_ids:
                        logger.info("Scraping %s race %s", site.value, race_id)
                        race = await scraper.scrape(race_id)
                        all_races.append(race)
                else:
                    # TODO: 最新レースの自動取得を実装
                    logger.warning(
                        "No race IDs specified, skipping scraping",
                        extra={"site": site.value},
                    )
            finally:
                await client.close()

        return all_races


async def run_data_update_job(
    *,
    sites: list[ScrapingSite] | None = None,
    race_ids: list[str] | None = None,
    trigger_model_training: bool = True,
) -> JobResult:
    """データ更新ジョブを実行する（非同期関数）。"""
    job = DataUpdateJob(
        sites=sites,
        race_ids=race_ids,
        trigger_model_training=trigger_model_training,
    )
    return await job.run()


def notify_admins(
    db: Session,
    result: JobResult,
    *,
    job_name: str = "データ更新ジョブ",
) -> None:
    """管理者ユーザーにジョブ結果を通知する。"""
    # 管理者ユーザーを取得
    admin_params = user_crud.UserListParams(
        limit=100,
        offset=0,
        is_superuser=True,
        is_active=True,
    )
    admin_result = user_crud.list_users(db, admin_params)
    admins = admin_result.items

    if not admins:
        logger.warning("No admin users found for notification")
        return

    # 通知ディスパッチャを初期化
    settings = get_settings()
    push_sender = None
    if (
        settings.notification_vapid_private_key
        and settings.notification_vapid_public_key
        and settings.notification_vapid_subject
    ):
        from app.services.notification_dispatcher import PyWebPushSender

        push_sender = PyWebPushSender(
            vapid_private_key=settings.notification_vapid_private_key,
            vapid_public_key=settings.notification_vapid_public_key,
            subject=settings.notification_vapid_subject,
        )

    dispatcher = NotificationDispatcher(
        db,
        push_sender=push_sender,
        default_max_retries=settings.notification_default_max_retries,
    )

    # 通知メッセージを生成
    if result.status == JobStatus.SUCCESS:
        title = f"{job_name}が正常に完了しました"
        message = result.message
    elif result.status == JobStatus.PARTIAL:
        title = f"{job_name}が部分的に完了しました"
        message = result.message
    else:
        title = f"{job_name}が失敗しました"
        message = result.message
        if result.error:
            message += f"\nエラー: {result.error}"

    # 各管理者に通知を送信
    for admin in admins:
        try:
            from app.services.notification_dispatcher import NotificationEvent

            event = NotificationEvent(
                user_id=admin.id,
                category=NotificationCategory.SYSTEM,
                title=title,
                message=message,
                metadata={
                    "job_status": result.status.value,
                    "duration_seconds": result.duration_seconds,
                    **result.metadata,
                },
            )
            dispatcher.dispatch_event(event)
            logger.info(
                "Notification sent to admin",
                extra={"admin_id": admin.id, "job_status": result.status.value},
            )
        except Exception as exc:
            logger.exception(
                "Failed to send notification to admin",
                extra={"admin_id": admin.id},
                exc_info=exc,
            )

    db.commit()


__all__ = [
    "DataUpdateJob",
    "JobResult",
    "JobStatus",
    "notify_admins",
    "run_data_update_job",
]

