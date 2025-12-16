from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from app.application.customer.read_models import CustomerDetailReadModel
from app.domain.customer.enums import CustomerStatus
from app.domain.activity.enums import ActivityType
from app.domain.opportunity.enums import OpportunityStatus
from app.application.customer.read_models import CustomerBasicReadModel


class CustomerSummaryResponse(BaseModel):
    id: int
    email: str
    name: str
    status: CustomerStatus
    shop_id: int
    shop_name: str
    assigned_to_user_id: Optional[int]
    assigned_to_user_name: Optional[str]
    visit_count: int
    last_visit_at: Optional[datetime]
    created_at: datetime


class CustomerListResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    customer_summaries: list[CustomerSummaryResponse]


class ActivitySummaryResponse(BaseModel):
    id: int
    type: str
    subject: str
    scheduled_at: Optional[datetime]
    created_by_user_id: int
    created_at: datetime


class NoteSummaryResponse(BaseModel):
    id: int
    body: str
    created_by_user_id: int
    created_at: datetime


class OpportunityStageSummaryResponse(BaseModel):
    id: int
    name: str
    is_won: bool
    is_lost: bool


class OpportunitySummaryResponse(BaseModel):
    id: int
    title: str
    amount: Optional[float]
    probability: Optional[int]
    status: str
    expected_close_date: Optional[datetime]
    stage: Optional[OpportunityStageSummaryResponse]


class CustomerDetailResponse(BaseModel):
    id: int
    email: str
    name: str
    status: str
    created_at: datetime

    shop_id: int
    shop_name: str

    visit_count: int
    last_visit_at: Optional[datetime]

    recent_activities: list[ActivitySummaryResponse]
    recent_notes: list[NoteSummaryResponse]
    opportunities: list[OpportunitySummaryResponse]

    @classmethod
    def from_read_model(cls, rm: CustomerDetailReadModel) -> "CustomerDetailResponse":
        s = rm.summary  # CustomerSummaryReadModel

        return cls(
            id=s.id,
            email=s.email,
            name=s.name,
            status=s.status.value if isinstance(s.status, CustomerStatus) else str(s.status),
            created_at=s.created_at,
            shop_id=s.shop_id,
            shop_name=s.shop_name,
            visit_count=s.visit_count,
            last_visit_at=s.last_visit_at,
            recent_activities=[
                ActivitySummaryResponse(
                    id=a.id,
                    type=a.type.value if isinstance(a.type, ActivityType) else str(a.type),
                    subject=a.subject,
                    scheduled_at=a.scheduled_at,
                    created_by_user_id=a.created_by_user_id,
                    created_at=a.created_at,
                )
                for a in rm.recent_activities
            ],
            recent_notes=[
                NoteSummaryResponse(
                    id=n.id,
                    body=n.body,
                    created_by_user_id=n.created_by_user_id,
                    created_at=n.created_at,
                )
                for n in rm.recent_notes
            ],
            opportunities=[
                OpportunitySummaryResponse(
                    id=o.id,
                    title=o.title,
                    amount=o.amount,
                    probability=o.probability,
                    status=(o.status.value if isinstance(o.status, OpportunityStatus) else str(o.status)),
                    expected_close_date=o.expected_close_date,
                    stage=(
                        OpportunityStageSummaryResponse(
                            id=o.stage.id,
                            name=o.stage.name,
                            is_won=o.stage.is_won,
                            is_lost=o.stage.is_lost,
                        )
                        if o.stage is not None
                        else None
                    ),
                )
                for o in rm.opportunities
            ],
        )


class CreateCustomerRequest(BaseModel):
    """顧客作成用のリクエストボディ."""

    # 0 などは無効。1 以上の整数のみ許可
    shop_id: int = Field(..., ge=1, description="顧客が所属する店舗ID（1以上）")
    # EmailStr で形式チェック + DB カラム長（255）に合わせて長さも制限
    email: EmailStr = Field(..., max_length=255, description="顧客のメールアドレス")
    # 空文字は許可しない。最大 255 文字。前後の空白は自動でトリム。
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        json_schema_extra={"strip_whitespace": True},
        description="顧客名（1〜255文字）",
    )
    # Enum 自体がバリデーション兼ねるので追加制約は不要（default は ACTIVE）
    status: CustomerStatus = CustomerStatus.ACTIVE
    # 担当者IDを指定する場合は 1 以上の整数。未指定は None。
    assigned_to_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="担当営業ユーザーID（任意）",
    )


class UpdateCustomerRequest(BaseModel):
    """顧客更新（PATCH）のリクエストボディ.

    - どの項目も「任意」
    - None の場合は「今回の更新では変更しない」と解釈（application 層で制御）
    """

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="顧客名（未指定なら変更なし）",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="メールアドレス（未指定なら変更なし）",
    )
    status: Optional[CustomerStatus] = Field(
        default=None,
        description="顧客ステータス（ACTIVE / INACTIVE / LOST。未指定なら変更なし）",
    )
    assigned_to_user_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="担当者ユーザーID（未指定なら変更なし）",
    )


class CustomerBasicResponse(BaseModel):
    """顧客作成・更新などで返すシンプルな顧客情報."""

    id: int = Field(..., description="顧客ID", json_schema_extra={"example": 10})
    shop_id: int = Field(..., description="所属店舗ID", json_schema_extra={"example": 1})
    email: EmailStr = Field(
        ..., description="顧客のメールアドレス", json_schema_extra={"example": "new_customer@example.com"}
    )
    name: str = Field(..., description="顧客名", json_schema_extra={"example": "新規 顧客"})
    status: CustomerStatus = Field(..., description="顧客ステータス", json_schema_extra={"example": "ACTIVE"})
    assigned_to_user_id: Optional[int] = Field(
        default=None,
        description="担当営業ユーザーID（任意）",
        json_schema_extra={"example": 1},
    )
    created_at: datetime = Field(
        ..., description="作成日時", json_schema_extra={"example": "2025-01-10T10:00:00+09:00"}
    )
    updated_at: datetime = Field(
        ..., description="更新日時", json_schema_extra={"example": "2025-01-10T10:00:00+09:00"}
    )

    @classmethod
    def from_read_model(cls, rm: CustomerBasicReadModel) -> "CustomerBasicResponse":
        return cls(
            id=rm.id,
            shop_id=rm.shop_id,
            email=rm.email,
            name=rm.name,
            status=rm.status,
            assigned_to_user_id=rm.assigned_to_user_id,
            created_at=rm.created_at,
            updated_at=rm.updated_at,
        )
