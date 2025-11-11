"""API ルータの登録処理を提供する。"""

from fastapi import APIRouter, FastAPI

from app.api.routers import admin, auth, notifications, predictions, races, reference, users

api_router = APIRouter()
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(notifications.router)
api_router.include_router(predictions.router)
api_router.include_router(races.router)
api_router.include_router(reference.router)
api_router.include_router(users.router)


def register_routers(application: FastAPI, prefix: str = "") -> None:
    """アプリケーションに API ルータを登録する。"""
    application.include_router(api_router, prefix=prefix)


__all__ = ["api_router", "register_routers"]


