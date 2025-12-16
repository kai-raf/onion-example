from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime

from typing import Sequence

from app.domain.auth.enums import UserRoleName
from app.domain.user.errors import InactiveUserError


@dataclass
class User:
    """ドメインモデルとしてのユーザーエンティティ"""

    id: int
    email: str
    full_name: str
    hashed_password: str
    is_active: bool
    is_superuser: bool
    timezone: str
    roles: Sequence[UserRoleName]
    created_at: datetime
    updated_at: datetime

    # ★ ドメイン振る舞いを追加
    def ensure_active(self) -> None:
        """ユーザーがアクティブでない場合はドメイン例外を送出する。

        - アプリケーション側はこの例外をキャッチして
          「ログイン不可」「操作不可」といったユースケースの失敗にマッピングする。
        """
        if not self.is_active:
            raise InactiveUserError("User is inactive")
