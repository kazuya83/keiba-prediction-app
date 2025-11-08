import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routers import register_routers
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """FastAPI アプリケーションを初期化して返す。"""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
    )

    register_exception_handlers(application)
    register_routers(application, prefix=settings.api_prefix)

    return application


def register_exception_handlers(application: FastAPI) -> None:
    """共通例外ハンドラを登録する。"""

    @application.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception occurred",
            extra={"path": request.url.path, "method": request.method},
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )


app = create_app()


@app.get("/health", summary="ヘルスチェック", tags=["health"])
async def health_check() -> dict[str, str]:
    """アプリケーションの稼働確認を返す。"""
    return {"status": "ok"}


