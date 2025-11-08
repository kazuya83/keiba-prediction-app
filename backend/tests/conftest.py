"""pytest 用の共通フィクスチャを定義する。"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def test_client() -> Generator[TestClient, None, None]:
    """FastAPI アプリケーションの TestClient を提供する。"""
    with TestClient(app) as client:
        yield client


