from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.customer.enums import CustomerStatus
from app.domain.activity.enums import ActivityType
from app.domain.opportunity.enums import OpportunityStatus

"""
Title: 顧客一覧ユースケースの “結果の形（データ構造）” だけを定義するファイル

Description:
    ユースケースの「出口」を表現するモジュール。
    すべて「出力専用 DTO（ReadModel）」をここに集約

    - CustomerSummaryReadModel:
        顧客一覧の 1行分（id, name, email, shop_name, visit_count, …）
    - CustomerListResult:
        ページング情報付きの全体結果（total_count, page, page_size, customer_summaries）

Point:
    - 中身は dataclass だけ（ロジックは書かない）。
    - DB も HTTP も知らない、アプリ内部での結果の形を決める場所。
    - 「このユースケースの結果はこういう構造で返したい」という application 層の設計。
"""


@dataclass
class CustomerSummaryReadModel:
    """顧客サマリーのReadモデル"""

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


@dataclass
class CustomerListResult:
    """顧客一覧取得結果のReadモデル"""

    total_count: int
    page: int
    page_size: int
    customer_summaries: list[CustomerSummaryReadModel]


@dataclass
class ActivitySummaryReadModel:
    """顧客詳細における活動履歴のReadモデル"""

    id: int
    type: ActivityType
    subject: str
    scheduled_at: Optional[datetime]
    created_by_user_id: int
    created_at: datetime


@dataclass
class NoteSummaryReadModel:
    """顧客詳細におけるメモのReadモデル"""

    id: int
    body: str
    created_by_user_id: int
    created_at: datetime


@dataclass
class OpportunitySummaryReadModel:
    """顧客詳細における商談情報のReadモデル"""

    id: int
    title: str
    amount: Optional[float]
    probability: Optional[int]
    status: OpportunityStatus
    expected_close_date: Optional[datetime]
    stage: Optional[OpportunityStageSummaryReadModel]


@dataclass
class OpportunityStageSummaryReadModel:
    """顧客詳細における商談ステージのReadモデル"""

    id: int
    name: str
    is_won: bool
    is_lost: bool


@dataclass
class CustomerDetailReadModel:
    """顧客詳細のReadモデル"""

    summary: CustomerSummaryReadModel
    recent_activities: list[ActivitySummaryReadModel]
    recent_notes: list[NoteSummaryReadModel]
    opportunities: list[OpportunitySummaryReadModel]


@dataclass
class CustomerBasicReadModel:
    """単一顧客のベーシック情報（作成直後のレスポンスなどに利用）。

    - 一覧用サマリーほど重くない
    - 顧客詳細のヘッダ情報にも使い回せる前提
    """

    id: int
    shop_id: int
    email: str
    name: str
    status: CustomerStatus
    assigned_to_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
