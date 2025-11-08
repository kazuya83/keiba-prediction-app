"""
アプリケーション設定
"""
from pydantic_settings import BaseSettings
from typing import Optional, List, Union


class Settings(BaseSettings):
    """アプリケーション設定クラス"""
    
    # アプリケーション基本設定
    APP_NAME: str = "競馬予測アプリケーション"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API設定
    API_V1_PREFIX: str = "/api/v1"
    
    # データベース設定
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/keiba_db"
    
    # JWT設定
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS設定
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """CORSオリジンをリスト形式で返す"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # ロギング設定
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # スクレイピング設定
    SCRAPING_DELAY: float = 1.0  # リクエスト間隔（秒）
    SCRAPING_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # 機械学習設定
    ML_MODEL_PATH: str = "../ml/models"
    ML_PREDICTION_TIMEOUT: int = 60  # 予測タイムアウト（秒）
    
    # タスクスケジューラー設定
    DATA_UPDATE_HOUR: int = 3  # データ更新時刻（時）
    DATA_UPDATE_MINUTE: int = 0  # データ更新時刻（分）
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

