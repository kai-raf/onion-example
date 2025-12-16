from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import jwt

from app.application.auth.ports import TokenProvider
from app.core.config import settings  # 既存の Settings を利用


class JwtTokenProvider(TokenProvider):
    """PyJWT を使った TokenProvider 実装"""

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
    ) -> None:
        # デフォルトは Settings から取る。本番で key を変えたい場合は
        # DI で secret_key/algorithm を明示的に渡してもよい。
        self._secret_key = secret_key or settings.secret_key
        self._algorithm = algorithm or "HS256"

    def encode(
        self,
        payload: Mapping[str, Any],
        expires_in_minutes: int,
    ) -> str:
        """
        ペイロードから署名付き JWT を生成する。

        - iat（発行時刻）
        - exp（有効期限）
        を自動で付与する。
        """

        now = datetime.now(timezone.utc)
        to_encode: dict[str, Any] = dict(payload)

        # 発行時刻
        to_encode.setdefault("iat", int(now.timestamp()))

        # 有効期限
        expire = now + timedelta(minutes=expires_in_minutes)
        to_encode["exp"] = expire

        token = jwt.encode(
            to_encode,
            self._secret_key,
            algorithm=self._algorithm,
        )

        # PyJWT 2.x の encode は str を返す
        return token

    def decode(self, token: str) -> Mapping[str, Any]:
        """
        JWT を検証してペイロードを返す。

        - 期限切れ → jwt.ExpiredSignatureError
        - 署名不正 → jwt.InvalidSignatureError
        - その他トークン不正 → jwt.InvalidTokenError

        これらは AuthService 側でキャッチされ、
        TokenError にラップされる想定。
        """

        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={
                    "require": ["exp", "iat"],
                    "verify_exp": True,
                },
            )
            return payload
        except jwt.ExpiredSignatureError:
            # そのまま上に投げる。AuthService が catch して TokenError に変換。
            raise
        except jwt.InvalidTokenError:
            # 署名不正やフォーマット不正などまとめてここに来る
            raise
