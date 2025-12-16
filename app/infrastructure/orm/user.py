from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.activity import ActivityORM
    from app.infrastructure.orm.task import TaskORM
    from app.infrastructure.orm.audit_log import AuditLogORM
    from app.infrastructure.orm.shop import ShopORM
    from app.infrastructure.orm.customer import CustomerORM
    from app.infrastructure.orm.role import RoleORM


class UserORM(Base):
    """アプリケーションのユーザー（営業担当・マネージャー等）。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ユーザーID"
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="メールアドレス"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="氏名(フルネーム)"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="ハッシュ化パスワード"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="アクティブ状態"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="管理者権限"
    )
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Tokyo", nullable=False, comment="タイムゾーン"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="作成日時"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="更新日時"
    )
    version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="楽観的ロックバージョン"
    )
    roles: Mapped[List["RoleORM"]] = relationship(
        "RoleORM", secondary="user_roles", back_populates="users", lazy="selectin"
    )
    owned_shops: Mapped[List["ShopORM"]] = relationship(
        "ShopORM",
        back_populates="owner_user",
        lazy="selectin",
    )
    assigned_customers: Mapped[List["CustomerORM"]] = relationship(
        "CustomerORM",
        back_populates="assigned_to_user",
        lazy="selectin",
    )
    created_activities: Mapped[List["ActivityORM"]] = relationship(
        "ActivityORM",
        back_populates="created_by_user",
        foreign_keys="ActivityORM.created_by_user_id",
        lazy="selectin",
    )
    assigned_tasks: Mapped[List["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="assigned_to_user",
        foreign_keys="TaskORM.assigned_to_user_id",
        lazy="selectin",
    )
    created_tasks: Mapped[List["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="created_by_user",
        foreign_keys="TaskORM.created_by_user_id",
        lazy="selectin",
    )
    audit_logs: Mapped[List["AuditLogORM"]] = relationship(
        "AuditLogORM",
        back_populates="user",
        lazy="selectin",
    )
