from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shop.enums import ShopStatus

if TYPE_CHECKING:
    from app.infrastructure.orm.customer import CustomerORM
    from app.infrastructure.orm.user import UserORM
    from app.infrastructure.orm.reservation import ReservationORM


class ShopORM(Base):
    """店舗(拠点)情報"""

    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="店舗ID"
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="店舗コード"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="店舗名")
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="住所")
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="電話番号")
    status: Mapped[ShopStatus] = mapped_column(
        SAEnum(ShopStatus, native_enum=False),
        nullable=False,
        default=ShopStatus.ACTIVE,
        comment="店舗ステータス",
    )
    owner_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="店舗責任者ユーザーID",
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

    # リレーションシップ
    owner_user: Mapped[Optional[UserORM]] = relationship(
        "UserORM",
        back_populates="owned_shops",
    )
    customers: Mapped[List["CustomerORM"]] = relationship(
        "CustomerORM",
        back_populates="shop",
        lazy="selectin",
    )
    reservations: Mapped[List["ReservationORM"]] = relationship(
        "ReservationORM",
        back_populates="shop",
        lazy="selectin",
    )
