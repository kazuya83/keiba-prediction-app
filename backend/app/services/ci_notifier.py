"""CI結果通知サービス。"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CINotifier:
    """CI結果を通知するサービスクラス。"""

    def __init__(self, *, notification_url: str | None = None) -> None:
        """CINotifierを初期化する。

        Args:
            notification_url: 通知APIのURL（Noneの場合は設定から取得）
        """
        self._notification_url = notification_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def notify_ci_result(
        self,
        *,
        status: str,
        jobs: dict[str, str],
        commit_sha: str | None = None,
        branch: str | None = None,
        workflow_url: str | None = None,
    ) -> bool:
        """CI結果を通知する。

        Args:
            status: 全体のステータス（"success" または "failure"）
            jobs: ジョブ名とステータスの辞書
            commit_sha: コミットSHA
            branch: ブランチ名
            workflow_url: ワークフローのURL

        Returns:
            通知が成功したかどうか
        """
        url = self._notification_url or get_settings().notification_api_url
        if not url:
            logger.warning("Notification API URL is not configured")
            return False

        message = self._build_message(status, jobs, commit_sha, branch, workflow_url)

        try:
            response = await self._client.post(
                url,
                json={
                    "message": message,
                    "status": status,
                    "jobs": jobs,
                    "commit_sha": commit_sha,
                    "branch": branch,
                    "workflow_url": workflow_url,
                },
            )
            response.raise_for_status()
            logger.info("CI notification sent successfully")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send CI notification: {e}")
            return False

    def _build_message(
        self,
        status: str,
        jobs: dict[str, str],
        commit_sha: str | None,
        branch: str | None,
        workflow_url: str | None,
    ) -> str:
        """通知メッセージを構築する。

        Args:
            status: 全体のステータス
            jobs: ジョブ名とステータスの辞書
            commit_sha: コミットSHA
            branch: ブランチ名
            workflow_url: ワークフローのURL

        Returns:
            通知メッセージ
        """
        status_emoji = "✅" if status == "success" else "❌"
        status_text = "成功" if status == "success" else "失敗"

        lines: list[str] = []
        lines.append(f"CI結果: {status_emoji} {status_text}")

        if branch:
            lines.append(f"ブランチ: {branch}")

        if commit_sha:
            short_sha = commit_sha[:7]
            lines.append(f"コミット: {short_sha}")

        lines.append("")
        lines.append("ジョブ結果:")

        for job_name, job_status in jobs.items():
            emoji = "✅" if job_status == "success" else "❌"
            status_display = "成功" if job_status == "success" else "失敗"
            lines.append(f"  {emoji} {job_name}: {status_display}")

        if workflow_url:
            lines.append("")
            lines.append(f"詳細: {workflow_url}")

        return "\n".join(lines)

    async def close(self) -> None:
        """クライアントを閉じる。"""
        await self._client.aclose()

