"""
FastAPIアプリケーションのエントリーポイント
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.core.config import settings

# ロギング設定
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL,
)

# FastAPIアプリケーションの作成
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# エラーハンドリング
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    グローバル例外ハンドラー
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "healthy", "version": settings.APP_VERSION}


# ルートエンドポイント
@app.get("/")
async def root():
    """
    ルートエンドポイント
    """
    return {
        "message": "競馬予測アプリケーション API",
        "version": settings.APP_VERSION,
    }


# APIルーターのインポート（今後実装）
# from app.api import auth, races, predictions, notifications, admin
# app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["認証"])
# app.include_router(races.router, prefix=settings.API_V1_PREFIX, tags=["レース"])
# app.include_router(predictions.router, prefix=settings.API_V1_PREFIX, tags=["予測"])
# app.include_router(notifications.router, prefix=settings.API_V1_PREFIX, tags=["通知"])
# app.include_router(admin.router, prefix=settings.API_V1_PREFIX, tags=["管理者"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

