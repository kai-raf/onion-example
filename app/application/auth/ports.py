from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol

from app.domain.user.models import User


class UserRepository(Protocol):
    """ユーザー取得のためのポート（抽象リポジトリ）

    実装例: SqlAlchemyUserRepository（infrastructure 層）
    """

    def get_by_email(self, email: str) -> Optional[User]:
        """メールアドレスでユーザーを1件取得。見つからなければ None を返す。"""
        ...

    def get_by_id(self, user_id: int) -> Optional[User]:
        """IDでユーザーを1件取得。見つからなければ None を返す。"""
        ...


class PasswordHasher(Protocol):
    """パスワードハッシュ/検証用のポート

    実装例: Argon2PasswordHasher
    """

    def hash(self, plain_password: str) -> str:
        """平文パスワードからハッシュを生成する。"""
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """平文とハッシュを比較し、一致していれば True を返す。"""
        ...


class TokenProvider(Protocol):
    """アクセストークン（JWT など）の発行・検証を抽象化するポート

    実装例: JwtTokenProvider（PyJWT + settings による SECRET_KEY / ALGORITHM / 有効期限）
    """

    def encode(
        self,
        payload: Mapping[str, Any],
        expires_in_minutes: int,
    ) -> str:
        """
        任意のペイロードからトークン文字列を発行する。

        例: payload = {"sub": str(user.id), "email": user.email}
        """
        ...

    def decode(self, token: str) -> Mapping[str, Any]:
        """
        トークン文字列を検証し、ペイロードを返す。

        不正トークン / 期限切れなどの場合は、実装側で適切な例外
        （例: TokenDecodeError）を投げる想定。
        """
        ...
