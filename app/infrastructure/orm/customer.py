from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    String,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.activity import ActivityORM
    from app.infrastructure.orm.task import TaskORM
    from app.infrastructure.orm.opportunity import OpportunityORM
    from app.infrastructure.orm.note import NoteORM
    from app.infrastructure.orm.reservation import ReservationORM
    from app.infrastructure.orm.shop import ShopORM
    from app.infrastructure.orm.user import UserORM

from app.domain.customer.enums import CustomerStatus


class CustomerORM(Base):
    """顧客情報。"""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="顧客ID"
    )
    shop_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属店舗ID",
    )

    external_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True, comment="外部システム連携用コード"
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="顧客名")
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="メールアドレス"
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="電話番号"
    )

    status: Mapped[CustomerStatus] = mapped_column(
        SAEnum(CustomerStatus, native_enum=False),
        nullable=False,
        default=CustomerStatus.ACTIVE,
        comment="顧客ステータス",
    )

    rank: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="顧客ランク(A/B/Cなど)"
    )

    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True, comment="担当ユーザーID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="作成日時"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="更新日時"
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="楽観的ロックバージョン"
    )

    shop: Mapped[ShopORM] = relationship(
        "ShopORM",
        back_populates="customers",
    )

    assigned_to_user: Mapped[Optional[UserORM]] = relationship(
        "UserORM",
        back_populates="assigned_customers",
    )

    reservations: Mapped[List["ReservationORM"]] = relationship(
        "ReservationORM",
        back_populates="customer",
        lazy="selectin",
    )

    activities: Mapped[List["ActivityORM"]] = relationship(
        "ActivityORM",
        back_populates="customer",
        lazy="selectin",
    )

    opportunities: Mapped[List["OpportunityORM"]] = relationship(
        "OpportunityORM",
        back_populates="customer",
        lazy="selectin",
    )

    tasks: Mapped[List["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="customer",
        lazy="selectin",
    )

    notes: Mapped[List["NoteORM"]] = relationship(
        "NoteORM",
        back_populates="customer",
        lazy="selectin",
    )
