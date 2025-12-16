# app/domain/user/errors.py
from __future__ import annotations


class UserDomainError(Exception):
    """User ドメインに関する例外のベースクラス。"""

    pass


class InactiveUserError(UserDomainError):
    """非アクティブなユーザーに対する操作が行われたときのドメイン例外。"""

    def __init__(self, message: str = "User is inactive") -> None:
        super().__init__(message)
