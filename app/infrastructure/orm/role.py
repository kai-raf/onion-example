from __future__ import annotations
from app.infrastructure.db.base import Base

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.auth.enums import UserRoleName

if TYPE_CHECKING:
    from app.infrastructure.orm.user import UserORM


class RoleORM(Base):
    """ユーザーロール（権限単位のまとまり）。"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ロールID"
    )
    name: Mapped[UserRoleName] = mapped_column(
        SAEnum(UserRoleName, native_enum=False), unique=True, nullable=False, comment="ロール名"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="ロール説明")

    users: Mapped[List[UserORM]] = relationship(
        "UserORM",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )


class UserRoleORM(Base):
    """ユーザーとロールの多対多中間テーブル。"""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),)

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ユーザーロールID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="ユーザーID"
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True, comment="ロールID"
    )
