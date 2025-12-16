from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    Enum as SAEnum,
    Text,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.customer import CustomerORM
    from app.infrastructure.orm.opportunity import OpportunityORM
    from app.infrastructure.orm.user import UserORM

from app.domain.task.enums import TaskStatus


class TaskORM(Base):
    """タスク（ToDo）。"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="タスクID"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="タスクタイトル")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="詳細説明")

    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, native_enum=False),
        nullable=False,
        default=TaskStatus.TODO,
        comment="タスクステータス",
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="期限日時"
    )

    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, comment="関連顧客ID"
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        nullable=True,
        comment="関連商談ID",
    )

    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True, comment="担当ユーザーID"
    )
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="作成ユーザーID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="作成日時"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="更新日時"
    )

    customer: Mapped[Optional[CustomerORM]] = relationship(
        "CustomerORM",
        back_populates="tasks",
    )

    opportunity: Mapped[Optional[OpportunityORM]] = relationship(
        "OpportunityORM",
        back_populates="tasks",
    )

    assigned_to_user: Mapped[Optional[UserORM]] = relationship(
        "UserORM",
        back_populates="assigned_tasks",
        foreign_keys=[assigned_to_user_id],
    )

    created_by_user: Mapped[UserORM] = relationship(
        "UserORM",
        back_populates="created_tasks",
        foreign_keys=[created_by_user_id],
    )
