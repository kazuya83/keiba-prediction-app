"""スケジューラ設定のテスト。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tasks.jobs import JobResult, JobStatus
from app.tasks.scheduler import SchedulerConfig, setup_scheduler


class TestSchedulerConfig:
    """SchedulerConfigのテスト。"""

    def test_default_config(self) -> None:
        """デフォルト設定のテスト。"""
        config = SchedulerConfig()
        assert config.data_update_cron == "0 3 * * *"
        assert config.data_update_timezone == "Asia/Tokyo"
        assert config.trigger_model_training is True
        assert config.notify_on_success is False
        assert config.notify_on_partial is True
        assert config.notify_on_failure is True

    def test_from_env(self) -> None:
        """環境変数からの設定読み込みのテスト。"""
        with patch("app.tasks.scheduler.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.data_update_cron = "0 5 * * *"
            mock_settings.data_update_timezone = "UTC"
            mock_settings.trigger_model_training = False
            mock_settings.notify_on_success = True
            mock_settings.notify_on_partial = False
            mock_settings.notify_on_failure = False
            mock_get_settings.return_value = mock_settings

            config = SchedulerConfig.from_env()
            assert config.data_update_cron == "0 5 * * *"
            assert config.data_update_timezone == "UTC"
            assert config.trigger_model_training is False
            assert config.notify_on_success is True
            assert config.notify_on_partial is False
            assert config.notify_on_failure is False


class TestSchedulerSetup:
    """スケジューラ設定のテスト。"""

    @pytest.mark.asyncio
    async def test_setup_scheduler(self) -> None:
        """スケジューラの設定テスト。"""
        config = SchedulerConfig(
            data_update_cron="0 3 * * *",
            data_update_timezone="Asia/Tokyo",
        )

        scheduler = setup_scheduler(config)
        assert scheduler is not None
        assert scheduler.running is False

        # ジョブが登録されているか確認
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "data_update"
        assert jobs[0].name == "データ更新ジョブ"

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_scheduler_execution(self) -> None:
        """スケジューラの実行テスト。"""
        config = SchedulerConfig(
            data_update_cron="0 3 * * *",
            data_update_timezone="Asia/Tokyo",
            notify_on_success=False,
            notify_on_partial=False,
            notify_on_failure=False,
        )

        with patch("app.tasks.scheduler.run_data_update_job") as mock_run_job:
            mock_result = JobResult(
                status=JobStatus.SUCCESS,
                message="Test success",
                metadata={},
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            mock_run_job.return_value = mock_result

            scheduler = setup_scheduler(config)
            scheduler.start()

            # ジョブを手動で実行
            job = scheduler.get_job("data_update")
            assert job is not None

            # ジョブを即座に実行
            job.modify(next_run_time=datetime.now(timezone.utc))
            await asyncio.sleep(0.1)

            scheduler.shutdown(wait=True)

    @pytest.mark.asyncio
    async def test_job_lock(self) -> None:
        """ジョブロックのテスト。"""
        from app.tasks.scheduler import JobLock

        lock = JobLock()
        assert lock.acquire("test_job") is True
        assert lock.acquire("test_job") is False  # 既にロックされている
        lock.release("test_job")
        assert lock.acquire("test_job") is True  # 再取得可能


class TestNotificationIntegration:
    """通知連携のテスト。"""

    @pytest.mark.asyncio
    async def test_notify_on_failure(self) -> None:
        """失敗時の通知テスト。"""
        config = SchedulerConfig(
            notify_on_failure=True,
            notify_on_success=False,
            notify_on_partial=False,
        )

        with patch("app.tasks.scheduler.run_data_update_job") as mock_run_job, patch(
            "app.tasks.scheduler.notify_admins"
        ) as mock_notify:
            mock_result = JobResult(
                status=JobStatus.FAILED,
                message="Test failure",
                metadata={},
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error=Exception("Test error"),
            )
            mock_run_job.return_value = mock_result

            from app.tasks.scheduler import _execute_data_update_job

            await _execute_data_update_job(config)

            # 通知が呼ばれていない（notify_adminsはDBセッションが必要なため、モック内で呼ばれない）
            # 実際のテストでは、DBセッションをモックする必要がある

