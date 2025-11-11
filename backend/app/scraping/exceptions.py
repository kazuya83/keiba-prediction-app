"""スクレイピング処理で使用する共通例外定義。"""

from __future__ import annotations

from dataclasses import dataclass


class ScrapingError(Exception):
    """スクレイピング処理で発生する基底例外。"""


@dataclass(slots=True, frozen=True)
class FetchError(ScrapingError):
    """HTTP 取得処理で発生したエラー。"""

    url: str
    status_code: int | None = None
    message: str | None = None

    def __str__(self) -> str:
        if self.status_code is not None:
            return (
                f"FetchError(url={self.url}, status_code={self.status_code}, "
                f"message={self.message or 'HTTP error'})"
            )
        return f"FetchError(url={self.url}, message={self.message or 'HTTP error'})"


class ParseError(ScrapingError):
    """HTML 解析失敗時に送出される例外。"""


class RateLimitError(ScrapingError):
    """レート制限に関する例外。"""


__all__ = ["FetchError", "ParseError", "RateLimitError", "ScrapingError"]


