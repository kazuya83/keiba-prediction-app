"""スクレイピング処理で共通利用するユーティリティ関数群。"""

from __future__ import annotations

import re
from datetime import date, datetime, time

from bs4 import BeautifulSoup

GRADE_PATTERN = re.compile(r"\((G[1-3]|L|OP|重賞)\)")
DATE_PATTERN = re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})")
START_TIME_PATTERN = re.compile(r"(\d{1,2}):(\d{2})")
COURSE_PATTERN = re.compile(r"(芝|ダート|障害)[^\d]*(\d+)")


def strip_html(text: str) -> str:
    """HTML を含むテキストをプレーンテキストへ変換する。"""
    soup = BeautifulSoup(text, "lxml")
    return soup.get_text(separator=" ", strip=True)


def normalize_text(value: str | None) -> str:
    """全角スペースなどを除去し、前後空白を整形する。"""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value.replace("\u3000", " ")).strip()


def parse_date(text: str) -> date:
    """文字列から日付を抽出する。"""
    match = DATE_PATTERN.search(text)
    if match is None:
        raise ValueError(f"日付を解析できません: {text}")
    year, month, day = map(int, match.groups())
    return date(year, month, day)


def parse_start_time(base_date: date, text: str) -> datetime | None:
    """開始時刻文字列から datetime を生成する。"""
    match = START_TIME_PATTERN.search(text)
    if match is None:
        return None
    hour, minute = map(int, match.groups())
    return datetime.combine(base_date, time(hour=hour, minute=minute))


def parse_course(text: str) -> tuple[str, int]:
    """コース種別と距離を抽出する。"""
    match = COURSE_PATTERN.search(text)
    if match is None:
        raise ValueError(f"コース情報を解析できません: {text}")
    course_type = match.group(1)
    distance = int(match.group(2))
    return course_type, distance


def parse_grade_from_name(name: str) -> str | None:
    """レース名からグレードを推定する。"""
    match = GRADE_PATTERN.search(name)
    if match is None:
        return None
    return match.group(1)


__all__ = [
    "normalize_text",
    "parse_course",
    "parse_date",
    "parse_grade_from_name",
    "parse_start_time",
    "strip_html",
]


