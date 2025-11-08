from fastapi import FastAPI

app = FastAPI(
    title="Keiba Prediction API",
    description="競馬予測アプリケーションのバックエンド API",
    version="0.1.0",
)


@app.get("/health", summary="ヘルスチェック", tags=["health"])
async def health_check() -> dict[str, str]:
    """アプリケーションの稼働確認を返す。"""
    return {"status": "ok"}

