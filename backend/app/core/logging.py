"""アプリケーションのロギング設定と管理者向けログストレージを定義する。"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

DEFAULT_LOG_RECORD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}

DEFAULT_STORAGE_CAPACITY = 500


@dataclass(slots=True, frozen=True)
class StoredLogRecord:
    """保持されるログレコードのシリアライズ済み表現。"""

    record_id: int
    level: int
    level_name: str
    message: str
    logger_name: str
    pathname: str
    lineno: int
    created_at: datetime
    context: dict[str, Any]
    exception: str | None


class AdminLogStorage:
    """管理者向けのエラーログを保持するストレージ。"""

    def __init__(self, capacity: int = DEFAULT_STORAGE_CAPACITY) -> None:
        self._capacity = max(capacity, 1)
        self._records: deque[StoredLogRecord] = deque(maxlen=self._capacity)
        self._lock = Lock()
        self._sequence = 0

    def append(self, record: StoredLogRecord) -> None:
        """新しいログレコードを保存する。"""
        with self._lock:
            self._records.appendleft(record)

    def next_sequence(self) -> int:
        """連番 ID を発行する。"""
        with self._lock:
            self._sequence += 1
            return self._sequence

    def list_records(
        self,
        *,
        min_level: int = logging.ERROR,
        limit: int = 100,
        since: datetime | None = None,
    ) -> list[StoredLogRecord]:
        """保持しているログをフィルタリングして返す。"""
        if limit <= 0:
            return []
        normalized_since = self._normalize_datetime(since) if since else None

        with self._lock:
            snapshot = list(self._records)

        filtered: list[StoredLogRecord] = []
        for record in snapshot:
            if record.level < min_level:
                continue
            if normalized_since and record.created_at < normalized_since:
                continue
            filtered.append(record)
            if len(filtered) >= limit:
                break
        return filtered

    def reset(self) -> None:
        """ストレージを初期化する（主にテスト用）。"""
        with self._lock:
            self._records.clear()
            self._sequence = 0

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AdminLogHandler(logging.Handler):
    """エラーログをストレージへ記録するハンドラ。"""

    def __init__(self, storage: AdminLogStorage) -> None:
        super().__init__()
        self._storage = storage
        self._formatter = logging.Formatter()

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - ハンドラ例外はログに影響しないよう保護
        try:
            stored = self._to_stored_record(record)
        except Exception:
            self.handleError(record)
            return
        self._storage.append(stored)

    def _to_stored_record(self, record: logging.LogRecord) -> StoredLogRecord:
        created = datetime.fromtimestamp(record.created, tz=timezone.utc)
        message = record.getMessage()
        extra = _extract_extra_fields(record)

        if record.exc_info:
            exception_text = self._formatter.formatException(record.exc_info)
        else:
            exception_text = record.exc_text

        record_id = self._storage.next_sequence()
        return StoredLogRecord(
            record_id=record_id,
            level=record.levelno,
            level_name=record.levelname,
            message=message,
            logger_name=record.name,
            pathname=record.pathname,
            lineno=record.lineno,
            created_at=created,
            context=extra,
            exception=exception_text,
        )


_LOG_STORAGE = AdminLogStorage()
_CONFIGURED = False


def get_admin_log_storage() -> AdminLogStorage:
    """シングルトンのログストレージを返す。"""
    return _LOG_STORAGE


def configure_logging() -> None:
    """アプリケーション起動時にロギングを初期化する。"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = AdminLogHandler(_LOG_STORAGE)
    handler.setLevel(logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    _CONFIGURED = True


def _extract_extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in DEFAULT_LOG_RECORD_FIELDS
    }


__all__ = ["AdminLogStorage", "StoredLogRecord", "configure_logging", "get_admin_log_storage"]


