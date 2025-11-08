"""API ルータの登録処理を提供する。"""

from fastapi import APIRouter, FastAPI

api_router = APIRouter()


def register_routers(application: FastAPI, prefix: str = "") -> None:
    """アプリケーションに API ルータを登録する。"""
    application.include_router(api_router, prefix=prefix)


__all__ = ["api_router", "register_routers"]


