from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.customer import CustomerORM
    from app.infrastructure.orm.opportunity import OpportunityORM
    from app.infrastructure.orm.user import UserORM


class NoteORM(Base):
    """顧客や商談に紐づくメモ。"""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="メモID"
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, comment="関連顧客ID"
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, comment="関連商談ID"
    )

    body: Mapped[str] = mapped_column(Text, nullable=False, comment="メモ本文")

    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="作成ユーザーID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="作成日時"
    )

    customer: Mapped[Optional[CustomerORM]] = relationship(
        "CustomerORM",
        back_populates="notes",
    )

    opportunity: Mapped[Optional[OpportunityORM]] = relationship(
        "OpportunityORM",
        back_populates="notes",
    )

    created_by_user: Mapped[UserORM] = relationship(
        "UserORM",
        lazy="selectin",
    )
