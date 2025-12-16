from __future__ import annotations

from typing import Optional

from pwdlib import PasswordHash

from app.application.auth.ports import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """pwdlib[argon2] を使った PasswordHasher 実装"""

    def __init__(self, hasher: Optional[PasswordHash] = None) -> None:
        # recommended() は Argon2id ベースの安全なデフォルト設定を返してくれる
        self._hasher = hasher or PasswordHash.recommended()

    def hash(self, plain_password: str) -> str:
        """平文パスワードからハッシュを生成する。"""
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """平文とハッシュを比較し、一致していれば True を返す。"""
        try:
            return self._hasher.verify(plain_password, hashed_password)
        except Exception:
            # ハッシュ形式がおかしいなどの場合は False 扱い
            return False
