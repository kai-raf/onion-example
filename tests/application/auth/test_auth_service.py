# tests/application/auth/test_auth_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.application.auth.services import (
    AuthService,
    AuthSettings,
    AuthenticationError,
    TokenError,
)
from app.application.auth.ports import UserRepository, PasswordHasher, TokenProvider
from app.domain.user.models import User
from app.domain.auth.enums import UserRoleName


# ==========
# テスト用の Fake 実装
# ==========


class FakeUserRepository(UserRepository):
    def __init__(self, users_by_email: dict[str, User]) -> None:
        self._users_by_email = users_by_email

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)

    def get_by_id(self, user_id: int) -> User | None:
        for user in self._users_by_email.values():
            if user.id == user_id:
                return user
        return None


class FakePasswordHasher(PasswordHasher):
    def __init__(self, should_match: bool = True) -> None:
        self.should_match = should_match

    def hash(self, plain_password: str) -> str:
        # テスト用なので適当で良い
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        # テスト時に「マッチするかどうか」を外から制御したいので、フラグで返す
        return self.should_match


class FakeTokenProvider(TokenProvider):
    def __init__(self) -> None:
        self._stored_payload: dict[str, dict] = {}

    def encode(self, payload: dict, expires_in_minutes: int) -> str:
        token = "dummy-token"
        # 有効期限を付与して保存しておく（テスト用）
        now = datetime.now(timezone.utc)
        payload = dict(payload)
        payload["exp"] = now + timedelta(minutes=expires_in_minutes)
        self._stored_payload[token] = payload
        return token

    def decode(self, token: str) -> dict:
        if token not in self._stored_payload:
            raise TokenError("invalid token")
        return self._stored_payload[token]


# ==========
# テスト対象となる AuthService を組み立てるヘルパー
# ==========


def make_auth_service(
    users_by_email: dict[str, User],
    password_matches: bool = True,
) -> AuthService:
    user_repo = FakeUserRepository(users_by_email)
    password_hasher = FakePasswordHasher(should_match=password_matches)
    token_provider = FakeTokenProvider()
    settings = AuthSettings(access_token_expires_minutes=60)

    return AuthService(
        user_repo=user_repo,
        password_hasher=password_hasher,
        token_provider=token_provider,
        settings=settings,
    )


def make_active_user() -> User:
    """テスト用のアクティブなユーザーを1件作るヘルパー"""
    return User(
        id=1,
        email="taro@example.com",
        full_name="山田 太郎",
        hashed_password="hashed-password",  # FakePasswordHasher では実際には使わない
        is_active=True,
        is_superuser=True,
        timezone="Asia/Tokyo",
        roles=[UserRoleName.ADMIN],
        created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )


"""
概要：authenticate の正常系テスト
条件：
  - DB に「アクティブなユーザー」が 1 人だけいる
  - パスワード検証は成功する（FakePasswordHasher で制御）
期待：
  - AuthService.authenticate(email, password) を呼ぶと、その User が返る
  - 例外は出ない
"""


def test_authenticate_success() -> None:
    # Arrange: アクティブなユーザーが1人だけ存在する状態を作る
    user = make_active_user()
    service = make_auth_service(
        users_by_email={user.email: user},
        password_matches=True,  # FakePasswordHasher が常に verify=True を返すようにする
    )

    # Act: 正しい email / password で認証を実行
    result = service.authenticate(email=user.email, password="any-password")

    # Assert: 同じ User が返ってくること
    assert result == user


"""
概要：パスワード間違いのテスト
条件：
  - DB 上には taro@example.com のユーザーはいる（アクティブ）
  - ただし パスワード検証は失敗する ようにしたい
期待：
  - AuthService.authenticate(email, wrong_password) を呼ぶと、AuthenticationError が投げられる
"""


def test_authenticate_wrong_password() -> None:
    """パスワードが間違っている場合は AuthenticationError になること"""

    # Arrange: アクティブなユーザーは存在するが、パスワード検証は常に失敗する
    user = make_active_user()
    service = make_auth_service(
        users_by_email={user.email: user},
        password_matches=False,  # ★ FakePasswordHasher.verify が常に False を返すようになる
    )

    # Act & Assert: 認証を呼ぶと AuthenticationError が送出される
    with pytest.raises(AuthenticationError):
        service.authenticate(email=user.email, password="wrong-password")


"""
概要：非アクティブユーザーは認証NG
条件：
  - email は存在する
  - パスワードも正しい（password_matches=True）
  - ただし user.is_active = False
期待：
  - AuthService.authenticate(email, password) を呼ぶと AuthenticationError が投げられる
"""


def make_inactive_user() -> User:
    """テスト用の非アクティブユーザー"""
    user = make_active_user()
    user.is_active = False
    return user


def test_authenticate_inactive_user() -> None:
    """is_active=False のユーザーは認証できず AuthenticationError になること"""

    # Arrange: 非アクティブなユーザーが1人だけ存在する
    user = make_inactive_user()
    service = make_auth_service(
        users_by_email={user.email: user},
        password_matches=True,  # パスワード自体は正しい想定
    )

    # Act & Assert: 認証を呼ぶと AuthenticationError が送出される
    with pytest.raises(AuthenticationError):
        service.authenticate(email=user.email, password="any-password")


"""
概要：create_access_token → get_user_from_token の正常系
条件：
  - アクティブなユーザーが 1 人いる
  - AuthService.create_access_token(user) でトークンを発行
期待：
  - そのトークンを get_user_from_token(token) に渡すと 同じ User が返ってくる
"""


def test_get_user_from_token_success() -> None:
    """create_access_token で発行したトークンから同じユーザーが取得できること"""

    # Arrange: アクティブなユーザーと、それを返す AuthService
    user = make_active_user()
    service = make_auth_service(
        users_by_email={user.email: user},
        password_matches=True,
    )

    # Act: アクセストークンを発行し、そのトークンからユーザーを取得
    token = service.create_access_token(user)
    result = service.get_user_from_token(token.access_token)

    # Assert: 元のユーザーと同じであること
    assert result == user


"""
概要：create_access_token → get_user_from_token の正常系
条件：
  - アクティブなユーザーが 1 人いる
  - AuthService.create_access_token(user) でトークンを発行
期待：
  - そのトークンを get_user_from_token(token) に渡すと 同じ User が返ってくる
"""


def test_get_user_from_token_invalid_token() -> None:
    """不正なトークンを渡した場合は TokenError になること"""

    # Arrange: アクティブなユーザーが1人いるが、
    # トークンとしては存在しない文字列を渡す想定
    user = make_active_user()
    service = make_auth_service(
        users_by_email={user.email: user},
        password_matches=True,
    )

    # Act & Assert: 存在しないトークン文字列を渡すと TokenError が送出される
    with pytest.raises(TokenError):
        service.get_user_from_token("invalid-token")
