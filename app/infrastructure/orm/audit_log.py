from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.user import UserORM


class AuditLogORM(Base):
    """重要操作の監査ログ。"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="監査ログID"
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True, comment="実行ユーザーID"
    )

    action: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="操作種別(create_customer等)"
    )
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="操作対象エンティティ種別"
    )
    entity_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="操作対象エンティティID"
    )

    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="IPアドレス")
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="ユーザーエージェント"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="作成日時"
    )

    user: Mapped[Optional[UserORM]] = relationship(
        "UserORM",
        back_populates="audit_logs",
    )
