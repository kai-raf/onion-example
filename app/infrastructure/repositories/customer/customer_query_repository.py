from __future__ import annotations

from typing import Sequence, Tuple, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.application.customer.ports import CustomerQueryRepository, CustomerRepository
from app.application.customer.query_filter import CustomerFilter
from app.application.customer.read_models import (
    CustomerSummaryReadModel,
    CustomerDetailReadModel,
    ActivitySummaryReadModel,
    NoteSummaryReadModel,
    OpportunitySummaryReadModel,
    OpportunityStageSummaryReadModel,
)
from app.domain.user.models import User
from app.infrastructure.orm.customer import CustomerORM
from app.infrastructure.orm.shop import ShopORM
from app.infrastructure.orm.reservation import ReservationORM
from app.infrastructure.orm.activity import ActivityORM
from app.infrastructure.orm.note import NoteORM
from app.infrastructure.orm.opportunity import OpportunityORM, OpportunityStageORM

from app.domain.customer.models import Customer


class SqlAlchemyCustomerQueryRepository(CustomerQueryRepository):
    """SQLAlchemy を使って顧客サマリー一覧を取得する実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def fetch_customer_summaries(
        self,
        current_user: User,
        filters: CustomerFilter,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[CustomerSummaryReadModel]]:
        # 1. ベースクエリ（顧客 + 店舗 + 予約集計）
        base_query = (
            select(
                CustomerORM.id,
                CustomerORM.email,
                CustomerORM.name,
                CustomerORM.status,
                ShopORM.id.label("shop_id"),
                ShopORM.name.label("shop_name"),
                func.count(ReservationORM.id).label("visit_count"),
                func.max(ReservationORM.start_datetime).label("last_visit_at"),
                CustomerORM.created_at,
            )
            .join(ShopORM, ShopORM.id == CustomerORM.shop_id)
            .outerjoin(ReservationORM, ReservationORM.customer_id == CustomerORM.id)
            .group_by(
                CustomerORM.id,
                CustomerORM.email,
                CustomerORM.name,
                CustomerORM.status,
                CustomerORM.created_at,
                ShopORM.id,
                ShopORM.name,
            )
        )

        # 2. filters に応じて where 条件を追加（status, shop_id, keyword 等）
        # ステータス
        if filters.status is not None:
            base_query = base_query.where(CustomerORM.status == filters.status)

        # 店舗ID
        if filters.shop_id is not None:
            base_query = base_query.where(CustomerORM.shop_id == filters.shop_id)

        # 担当者（assigned_to_user_id）
        if filters.assigned_to_user_id is not None:
            base_query = base_query.where(CustomerORM.assigned_to_user_id == filters.assigned_to_user_id)

        # 名前 / メールアドレスのキーワード検索
        if filters.keyword:
            like = f"%{filters.keyword}%"
            base_query = base_query.where(
                or_(
                    CustomerORM.name.ilike(like),
                    CustomerORM.email.ilike(like),
                )
            )

        # 3. total_count（ページング前の件数）
        total_count_query = select(func.count()).select_from(base_query.subquery())
        total_count: int = self._session.execute(
            total_count_query
        ).scalar_one()  # scalar_oneで結果が必ず 1 行であるべき、という “契約” を保証できる

        # 4. ページングして rows 取得
        rows = (
            self._session.execute(base_query.limit(limit).offset(offset)).mappings().all()
        )  # mappings() で dict 形式で取れる, all() で全件を配列で取得

        # 5. ReadModel に詰め替え
        summaries: list[CustomerSummaryReadModel] = [
            CustomerSummaryReadModel(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                status=row["status"],
                shop_id=row["shop_id"],
                shop_name=row["shop_name"],
                assigned_to_user_id=None,  # 担当者 JOIN は後で
                assigned_to_user_name=None,
                visit_count=row["visit_count"] or 0,
                last_visit_at=row["last_visit_at"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

        return total_count, summaries

    def fetch_customer_detail(self, current_user: User, customer_id: int) -> Optional[CustomerDetailReadModel]:
        # ===========================
        # 1. 顧客基本情報 + 来店サマリ
        # ===========================
        base_query = (
            select(
                CustomerORM.id,
                CustomerORM.email,
                CustomerORM.name,
                CustomerORM.status,
                ShopORM.id.label("shop_id"),
                ShopORM.name.label("shop_name"),
                CustomerORM.created_at,
                func.count(ReservationORM.id).label("visit_count"),
                func.max(ReservationORM.start_datetime).label("last_visit_at"),
            )
            .join(ShopORM, ShopORM.id == CustomerORM.shop_id)
            .outerjoin(ReservationORM, ReservationORM.customer_id == CustomerORM.id)
            .where(CustomerORM.id == customer_id)
            .group_by(
                CustomerORM.id,
                CustomerORM.email,
                CustomerORM.name,
                CustomerORM.status,
                CustomerORM.created_at,
                ShopORM.id,
                ShopORM.name,
            )
        )

        base_row = self._session.execute(base_query).mappings().first()
        if base_row is None:
            # 顧客自体が存在しない
            return None

        summary = CustomerSummaryReadModel(
            id=base_row["id"],
            email=base_row["email"],
            name=base_row["name"],
            status=base_row["status"],  # CustomerStatus Enum のままでOK
            shop_id=base_row["shop_id"],
            shop_name=base_row["shop_name"],
            assigned_to_user_id=None,  # 必要になったら JOIN で拾う
            assigned_to_user_name=None,
            visit_count=base_row["visit_count"] or 0,
            last_visit_at=base_row["last_visit_at"],
            created_at=base_row["created_at"],
        )

        # ===========================
        # 2. 最近の活動履歴（最新5件）
        # ===========================
        RECENT_LIMIT = 5

        activities_query = (
            select(
                ActivityORM.id,
                ActivityORM.type,
                ActivityORM.subject,
                ActivityORM.scheduled_at,
                ActivityORM.created_at,
                ActivityORM.created_by_user_id,
            )
            .where(ActivityORM.customer_id == customer_id)
            .order_by(ActivityORM.created_at.desc())
            .limit(RECENT_LIMIT)
        )

        activity_rows = self._session.execute(activities_query).all()

        recent_activities = [
            ActivitySummaryReadModel(
                id=row.id,
                type=row.type,  # ActivityType Enum のはずなのでそのまま
                subject=row.subject,
                scheduled_at=row.scheduled_at,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
            )
            for row in activity_rows
        ]

        # ===========================
        # 3. 最近のメモ（最新5件）
        # ===========================
        notes_query = (
            select(
                NoteORM.id,
                NoteORM.body,
                NoteORM.created_at,
                NoteORM.created_by_user_id,
            )
            .where(NoteORM.customer_id == customer_id)
            .order_by(NoteORM.created_at.desc())
            .limit(RECENT_LIMIT)
        )

        note_rows = self._session.execute(notes_query).all()

        recent_notes = [
            NoteSummaryReadModel(
                id=row.id,
                body=row.body,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
            )
            for row in note_rows
        ]

        # ===========================
        # 4. 商談サマリ（最新5件）
        # ===========================
        opportunities_query = (
            select(
                OpportunityORM.id,
                OpportunityORM.title,
                OpportunityORM.amount,
                OpportunityORM.probability,
                OpportunityORM.status,
                OpportunityORM.expected_close_date,
                OpportunityStageORM.id.label("stage_id"),
                OpportunityStageORM.name.label("stage_name"),
                OpportunityStageORM.is_won,
                OpportunityStageORM.is_lost,
            )
            .outerjoin(
                OpportunityStageORM,
                OpportunityStageORM.id == OpportunityORM.stage_id,
            )
            .where(OpportunityORM.customer_id == customer_id)
            .order_by(OpportunityORM.created_at.desc())
            .limit(RECENT_LIMIT)
        )

        opp_rows = self._session.execute(opportunities_query).mappings().all()

        opportunities: list[OpportunitySummaryReadModel] = []
        for row in opp_rows:
            stage_rm: OpportunityStageSummaryReadModel | None = None
            if row["stage_id"] is not None:
                stage_rm = OpportunityStageSummaryReadModel(
                    id=row["stage_id"],
                    name=row["stage_name"],
                    is_won=row["is_won"],
                    is_lost=row["is_lost"],
                )

            amount = row["amount"]
            opportunities.append(
                OpportunitySummaryReadModel(
                    id=row["id"],
                    title=row["title"],
                    amount=float(amount) if amount is not None else None,
                    probability=row["probability"],
                    status=(row["status"].value if hasattr(row["status"], "value") else str(row["status"])),
                    expected_close_date=row["expected_close_date"],
                    stage=stage_rm,
                )
            )

        # ===========================
        # 5. CustomerDetailReadModel にまとめて返す
        # ===========================
        return CustomerDetailReadModel(
            summary=summary,
            recent_activities=recent_activities,
            recent_notes=recent_notes,
            opportunities=opportunities,
        )
