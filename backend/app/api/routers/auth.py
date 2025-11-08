"""認証関連エンドポイントを提供するルータ。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from authlib.integrations.requests_client import OAuth2Session
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.core.config import get_settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_oauth_state,
    create_refresh_token,
    decode_oauth_state,
    hash_token,
    verify_password,
)
from app.crud import auth_token as auth_token_crud
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    OAuthLoginResponse,
    RefreshRequest,
    RegisterRequest,
    Token,
)
from app.schemas.user import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(
    db: Session,
    user: User,
    *,
    revoke_existing: bool = True,
) -> Token:
    """指定ユーザー向けに新しいアクセストークンとリフレッシュトークンを発行する。"""
    settings = get_settings()
    access_expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        user.id,
        expires_delta=access_expires_delta,
        additional_claims={
            "role": "admin" if user.is_superuser else "user",
            "email": user.email,
        },
    )

    refresh_token = create_refresh_token()
    refresh_token_hash = hash_token(refresh_token)
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.refresh_token_expire_minutes,
    )

    if revoke_existing:
        auth_token_crud.revoke_all_refresh_tokens(db, user.id)

    auth_token_crud.create_refresh_token(
        db,
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=refresh_expires_at,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_expires_delta.total_seconds()),
        token_type="bearer",
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="メールアドレスとパスワードでユーザー登録する",
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db_session),
) -> Token:
    """新規ユーザーを作成し、JWT を発行する。"""
    if user_crud.get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既に登録済みのメールアドレスです。",
        )

    user = user_crud.create_user(
        db,
        UserCreate(
            email=request.email,
            password=request.password,
        ),
    )
    return _issue_tokens(db, user)


@router.post(
    "/login",
    response_model=Token,
    summary="メールアドレスとパスワードでログインする",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db_session),
) -> Token:
    """既存ユーザーの認証を行う。"""
    user = user_crud.get_user_by_email(db, request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません。",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アカウントが無効化されています。",
        )
    return _issue_tokens(db, user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="リフレッシュトークンでアクセストークンを再発行する",
)
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db_session),
) -> Token:
    """リフレッシュトークンの検証とローテーションを行う。"""
    token_hash = hash_token(request.refresh_token)
    token_record = auth_token_crud.get_active_refresh_token(db, token_hash)
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンが無効です。",
        )

    user = user_crud.get_user(db, token_record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません。",
        )

    auth_token_crud.revoke_all_refresh_tokens(db, user.id)
    return _issue_tokens(db, user, revoke_existing=False)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="現在のセッションをログアウトする",
)
def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> Response:
    """リフレッシュトークンを失効させ、セッションを終了する。"""
    token_hash = hash_token(request.refresh_token)
    token_record = auth_token_crud.get_by_token_hash(db, token_hash)
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リフレッシュトークンが無効です。",
        )
    if token_record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他ユーザーのトークンは操作できません。",
        )

    if not token_record.revoked:
        auth_token_crud.revoke_token(db, token_record)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_google_oauth_client(state: str | None = None) -> OAuth2Session:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth の設定が完了していません。",
        )
    if not settings.google_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth のリダイレクトURIが設定されていません。",
        )

    return OAuth2Session(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scope=settings.google_scope,
        redirect_uri=settings.google_redirect_uri,
        state=state,
    )


@router.get(
    "/google/login",
    response_model=OAuthLoginResponse,
    summary="Google OAuth ログインを開始する",
)
def google_login() -> OAuthLoginResponse:
    """Google OAuth の認可 URL を生成する。"""
    settings = get_settings()
    state = create_oauth_state("google")
    client = _get_google_oauth_client(state=state)
    authorization_url, _ = client.create_authorization_url(
        settings.google_authorize_url,
        state=state,
        prompt="select_account",
    )
    return OAuthLoginResponse(authorization_url=authorization_url, state=state)


@router.get(
    "/google/callback",
    response_model=Token,
    summary="Google OAuth のコールバックを処理する",
)
def google_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db_session),
) -> Token:
    """Google OAuth の認証コードを処理し、JWT を発行する。"""
    try:
        payload = decode_oauth_state(state)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="state パラメータが不正です。",
        ) from exc

    if payload.get("sub") != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="想定されていない OAuth プロバイダです。",
        )

    settings = get_settings()
    client = _get_google_oauth_client(state=state)

    token_response = client.fetch_token(
        settings.google_token_url,
        code=code,
    )
    if "access_token" not in token_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google からアクセストークンを取得できませんでした。",
        )

    userinfo_response = client.get(settings.google_userinfo_url)
    userinfo = userinfo_response.json()
    email = userinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google アカウントのメールアドレスを取得できませんでした。",
        )

    user = user_crud.get_user_by_email(db, email)
    if user is None:
        random_password = secrets.token_urlsafe(16)
        user = user_crud.create_user(
            db,
            UserCreate(
                email=email,
                password=random_password,
            ),
        )

    return _issue_tokens(db, user)


__all__ = ["router"]


