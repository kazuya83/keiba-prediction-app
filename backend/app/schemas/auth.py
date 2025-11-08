"""認証関連の Pydantic スキーマ定義。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class Token(BaseModel):
    """アクセストークンとリフレッシュトークンを返却するレスポンス。"""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT 内部の主要クレームを表すスキーマ。"""

    sub: str
    exp: int
    type: str

    model_config = ConfigDict(extra="allow")


class LoginRequest(BaseModel):
    """メールアドレスとパスワードによるログインリクエスト。"""

    email: EmailStr
    password: str = Field(min_length=8)

    model_config = ConfigDict(extra="forbid")


class RegisterRequest(BaseModel):
    """アカウント登録リクエスト。"""

    email: EmailStr
    password: str = Field(min_length=8)

    model_config = ConfigDict(extra="forbid")


class LogoutRequest(BaseModel):
    """リフレッシュトークンの失効リクエスト。"""

    refresh_token: str

    model_config = ConfigDict(extra="forbid")


class RefreshRequest(BaseModel):
    """リフレッシュトークンによるトークン再発行リクエスト。"""

    refresh_token: str

    model_config = ConfigDict(extra="forbid")


class OAuthLoginResponse(BaseModel):
    """OAuth 認証開始時のレスポンス。"""

    authorization_url: HttpUrl
    state: str


class OAuthCallback(BaseModel):
    """OAuth プロバイダからのコールバックパラメータ。"""

    code: str
    state: str

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "LoginRequest",
    "LogoutRequest",
    "OAuthCallback",
    "OAuthLoginResponse",
    "RefreshRequest",
    "RegisterRequest",
    "Token",
    "TokenPayload",
]


