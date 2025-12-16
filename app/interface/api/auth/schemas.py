from __future__ import annotations

from typing import List, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    # 型チェック用。実行時には読み込まれない
    from app.application.auth.read_models import CurrentUserReadModel


# POST /api/auth/login の Body { "email": "...", "password": "..." } を受け取る型
class LoginRequest(BaseModel):
    email: str
    password: str


# ログイン成功時に返したい { "access_token": "xxx", "token_type": "bearer" }
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# /api/auth/me のレスポンス用
# application 層の CurrentUserReadModel → API レスポンスへの変換をfrom_read_model で一箇所にまとめてる
class CurrentUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    roles: List[str]
    is_superuser: bool

    @classmethod
    def from_read_model(cls, rm: "CurrentUserReadModel") -> "CurrentUserResponse":
        # application 層の read_model から API レスポンスへ変換する
        return cls(
            id=rm.id,
            email=rm.email,
            full_name=rm.full_name,
            roles=rm.roles,
            is_superuser=rm.is_superuser,
        )
