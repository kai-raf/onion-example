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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.shop import ShopORM
    from app.infrastructure.orm.customer import CustomerORM


from app.domain.reservation.enums import ReservationStatus


class ReservationORM(Base):
    """予約 / 来店情報。"""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="予約ID"
    )
    shop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True, comment="店舗ID"
    )
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="顧客ID",
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="開始日時"
    )
    end_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="終了日時"
    )

    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=ReservationStatus.BEFORE_VISIT.value,
        comment="予約ステータス",
    )

    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="メモ")

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
        back_populates="reservations",
    )

    customer: Mapped[CustomerORM] = relationship(
        "CustomerORM",
        back_populates="reservations",
    )
