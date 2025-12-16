"""
「認証まわりの入り口」を 1 か所にまとめる場所
infrastructure / application / interface 層の「配線」する層
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

# Cognitoなどを使う場合は OAuth2PasswordBearerを使用する
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.user.models import User

from app.application.auth.services import (
    AuthService,
    AuthSettings,
    AuthenticationError,
    TokenError,
)
from app.application.auth.ports import UserRepository, PasswordHasher, TokenProvider


from app.infrastructure.repositories.user.user_query_repository import SqlAlchemyQueryUserRepository
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.jwt_token_provider import JwtTokenProvider

from app.infrastructure.db.session import get_db

# OAuth2 の Bearer スキームを使う場合（ex: Cognito）
# FastAPI が Authorization: Bearer <token> から token だけ抜き出してくれる仕組み
# tokenUrl="/api/auth/login" は Swagger 用の情報（実際の動作には直接関係しませんが、URL は実装に合わせた方がきれい)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 単純なHTTP Bearer スキームを使う場合
bearer_scheme = HTTPBearer()


def get_auth_service(
    db: Annotated[Session, Depends(get_db)],
) -> AuthService:
    """
    AuthService を組み立てて返す依存関数。
    ここが「オニオンの外側 → 内側」へのDI のハブになるイメージ

    - DB セッション
    - UserRepository 実装
    - PasswordHasher 実装
    - TokenProvider 実装
    - AuthSettings（有効期限など）

    をまとめて AuthService に注入する。
    """

    user_repo: UserRepository = SqlAlchemyQueryUserRepository(db)
    password_hasher: PasswordHasher = Argon2PasswordHasher()
    token_provider: TokenProvider = JwtTokenProvider(
        secret_key=settings.secret_key,
        # algorithm を変えたい場合は Settings にフィールドを足してここで渡す
        # algorithm=settings.jwt_algorithm,
    )

    auth_settings = AuthSettings(
        access_token_expires_minutes=settings.access_token_expire_minutes,
    )

    return AuthService(
        user_repo=user_repo,
        password_hasher=password_hasher,
        token_provider=token_provider,
        settings=auth_settings,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Authorization: Bearer <token> から現在の User を解決する依存。
    ルーターで current_user: User = Depends(get_current_user) と書くイメージ
    customers などの 認証必須エンドポイント全部で再利用 する前提

    - トークン不正 / 期限切れ → 401
    - ユーザー不在 / 非アクティブ → 401
    """

    token = credentials.credentials  # "Bearer " の後ろの生トークンだけ取れる

    try:
        user = auth_service.get_user_from_token(token)
        return user
    except (TokenError, AuthenticationError):
        # 認証失敗時は 401 を返す（WWW-Authenticate: Bearer を付ける）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
