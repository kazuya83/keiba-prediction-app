"""ユーザー関連の Pydantic スキーマ定義。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """ユーザースキーマの共通項目。"""

    email: EmailStr
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")


class UserCreate(UserBase):
    """ユーザー作成時の入力スキーマ。"""

    password: str = Field(min_length=8)
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """ユーザー更新時の入力スキーマ。"""

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class UserRead(BaseModel):
    """ユーザー情報の出力スキーマ。"""

    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


