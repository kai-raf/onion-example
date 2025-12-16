from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.application.auth.ports import UserRepository
from app.domain.user.models import User
from app.domain.auth.enums import UserRoleName

from app.infrastructure.orm.user import UserORM
from app.infrastructure.orm.role import RoleORM


class SqlAlchemyQueryUserRepository(UserRepository):
    """UserRepository ポートの SQLAlchemy 実装"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> Optional[User]:
        """メールアドレスでユーザーを1件取得。見つからなければ None を返す。"""
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.roles))  # roles を一緒にロードする
            .where(UserORM.email == email)
            .limit(1)
        )

        result = self._session.execute(stmt)
        orm_user: Optional[UserORM] = result.unique().scalar_one_or_none()
        if orm_user is None:
            return None
        return self._to_domain_user(orm_user)

    def get_by_id(self, user_id: int) -> Optional[User]:
        """IDでユーザーを1件取得。見つからなければ None を返す。"""
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.roles))  # roles を一緒にロードする
            .where(UserORM.id == user_id)
            .limit(1)
        )
        result = self._session.execute(stmt)
        orm_user: Optional[UserORM] = result.unique().scalar_one_or_none()

        if orm_user is None:
            return None
        return self._to_domain_user(orm_user)

    # ==========
    # マッピング
    # ==========

    def _to_domain_user(self, orm_user: UserORM) -> User:
        """ORM の UserORM を domain の User に変換する。"""

        # RoleORM.name -> UserRoleName へ変換
        # UserRoleName が Enum の場合を想定（Literal の場合はそのまま role.name でもOK）
        role_names: list[UserRoleName] = [UserRoleName(role.name) for role in orm_user.roles]

        return User(
            id=orm_user.id,
            email=orm_user.email,
            full_name=orm_user.full_name,
            hashed_password=orm_user.hashed_password,
            is_active=orm_user.is_active,
            is_superuser=orm_user.is_superuser,
            timezone=orm_user.timezone,
            roles=role_names,
            created_at=orm_user.created_at,
            updated_at=orm_user.updated_at,
        )
