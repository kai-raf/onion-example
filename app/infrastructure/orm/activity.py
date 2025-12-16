from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    String,
    Enum as SAEnum,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.user import UserORM
    from app.infrastructure.orm.customer import CustomerORM

from app.domain.activity.enums import ActivityType


class ActivityORM(Base):
    """顧客に対する活動履歴（電話・訪問・メール等）。"""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="活動ID"
    )
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="顧客ID",
    )

    type: Mapped[ActivityType] = mapped_column(
        SAEnum(ActivityType, native_enum=False),
        nullable=False,
        comment="活動種別(電話/訪問/メールなど)",
    )

    subject: Mapped[str] = mapped_column(String(255), nullable=False, comment="件名")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="詳細説明")

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="予定日時",
    )
    # 実施時刻などを別途持ちたければ executed_at などを追加

    created_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="作成ユーザーID",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="作成日時"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="更新日時"
    )

    customer: Mapped[CustomerORM] = relationship(
        "CustomerORM",
        back_populates="activities",
    )

    created_by_user: Mapped[UserORM] = relationship(
        "UserORM",
        back_populates="created_activities",
    )
