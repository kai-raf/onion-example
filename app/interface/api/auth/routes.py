from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.user.models import User

from app.application.auth.services import AuthService, AuthenticationError
from app.application.auth.read_models import CurrentUserReadModel

from app.interface.api.auth.deps import get_auth_service, get_current_user
from app.interface.api.auth.schemas import (
    LoginRequest,
    TokenResponse,
    CurrentUserResponse,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    email + password でログインしてアクセストークンを発行する。
    """

    try:
        user: User = auth_service.authenticate(body.email, body.password)
    except AuthenticationError:
        # 認証失敗 → 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(user)

    return TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> CurrentUserResponse:
    """
    現在ログイン中のユーザー情報を返す。
    """

    rm: CurrentUserReadModel = auth_service.build_current_user_read_model(current_user)
    return CurrentUserResponse.from_read_model(rm)
