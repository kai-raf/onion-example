from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuthToken:
    """認証トークン情報を表すドメインモデル"""

    access_token: str
    token_type: str  # "bearer" など
