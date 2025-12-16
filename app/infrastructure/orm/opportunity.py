from __future__ import annotations
from app.infrastructure.db.base import Base

from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    String,
    Enum as SAEnum,
    Numeric,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.user import UserORM
    from app.infrastructure.orm.customer import CustomerORM
    from app.infrastructure.orm.task import TaskORM
    from app.infrastructure.orm.note import NoteORM

from app.domain.opportunity.enums import OpportunityStatus


class OpportunityStageORM(Base):
    """商談ステージ（見込み〜受注など）。"""

    __tablename__ = "opportunity_stages"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ステージID"
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="ステージ名"
    )
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="表示順序"
    )
    is_won: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="受注ステージ判定"
    )
    is_lost: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="失注ステージ判定"
    )

    opportunities: Mapped[List["OpportunityORM"]] = relationship(
        "OpportunityORM",
        back_populates="stage",
        lazy="selectin",
    )


class OpportunityORM(Base):
    """商談情報。"""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="商談ID"
    )
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="顧客ID",
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="商談タイトル")
    amount: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(12, 2), nullable=True, comment="商談金額"
    )
    probability: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="成約確度(0-100%)"
    )

    status: Mapped[OpportunityStatus] = mapped_column(
        SAEnum(OpportunityStatus, native_enum=False),
        nullable=False,
        default=OpportunityStatus.OPEN,
        comment="商談ステータス",
    )

    expected_close_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="成約予定日"
    )

    stage_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("opportunity_stages.id"), nullable=True, comment="商談ステージID"
    )

    owner_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="担当ユーザーID"
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

    customer: Mapped[CustomerORM] = relationship(
        "CustomerORM",
        back_populates="opportunities",
    )

    stage: Mapped[Optional[OpportunityStageORM]] = relationship(
        "OpportunityStageORM",
        back_populates="opportunities",
    )

    owner_user: Mapped[UserORM] = relationship(
        "UserORM",
        lazy="selectin",
    )

    tasks: Mapped[List["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="opportunity",
        lazy="selectin",
    )

    notes: Mapped[List["NoteORM"]] = relationship(
        "NoteORM",
        back_populates="opportunity",
        lazy="selectin",
    )
