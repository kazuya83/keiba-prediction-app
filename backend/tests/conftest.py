"""pytest 用の共通フィクスチャを定義する。"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db_session
from app.db.base import Base, import_all_models
from app.main import create_app

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """テスト用 SQLite エンジンを生成する。"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import_all_models()
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """テスト毎に分離された DB セッションを提供する。"""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionFactory = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI アプリケーションの TestClient を提供する。"""
    application = create_app()

    def _override_get_db_session() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            db_session.expire_all()

    application.dependency_overrides[get_db_session] = _override_get_db_session

    with TestClient(application) as client:
        yield client

    application.dependency_overrides.pop(get_db_session, None)


