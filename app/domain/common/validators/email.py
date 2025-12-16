from __future__ import annotations

from typing import Type


def validate_email(email: str, *, exception_cls: Type[Exception]) -> None:
    """簡易的な email 形式チェック。

    - どのドメインでも再利用できるように、投げる例外クラスは呼び出し元から渡す。
    """
    if "@" not in email:
        raise exception_cls("Invalid email format.")
