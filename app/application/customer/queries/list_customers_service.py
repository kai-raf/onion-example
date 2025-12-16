# app/application/customer/query_service.py
from __future__ import annotations

from dataclasses import dataclass

from app.application.customer.read_models import CustomerListResult
from app.domain.user.models import User
from app.domain.user.errors import InactiveUserError
from app.application.customer.ports import CustomerQueryRepository
from app.application.customer.query_filter import CustomerFilter
from app.application.common.errors import AuthorizationError

"""
Title: 「顧客一覧ユースケースそのもの（処理の本体）を書くファイル」

Description:
    「ログインユーザー視点の顧客一覧を取得する」という ユースケースのメイン処理。

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
class ListCustomersQueryService:
    """顧客一覧など、読み取り系ユースケースを提供するサービス。"""

    customer_query_repo: CustomerQueryRepository

    def list_customers(
        self,
        current_user: User,
        filters: CustomerFilter,
    ) -> CustomerListResult:
        """ログインユーザー視点の顧客一覧を取得するユースケース。

        - current_user が閲覧可能な顧客のみが対象
        - フィルター条件を補正（最小値・最大値など）
        - ページネーション情報を組み立てて返す
        """
        # 1. 認可・前提条件チェック
        # ★ アクティブかどうかのルールはドメインに委譲する
        try:
            current_user.ensure_active()
        except InactiveUserError as exc:
            # 「このユーザーはこの操作を行えない」という AuthorizationError にマッピング
            raise AuthorizationError("Inactive user") from exc

        # 2. ページ/ページサイズの正規化
        page = max(filters.page, 1)
        page_size = min(max(filters.page_size, 1), 100)  # 1〜100 の範囲に制限
        offset = (page - 1) * page_size

        if filters.assigned_to_me:
            effective_assigned_to_user_id = current_user.id
        else:
            effective_assigned_to_user_id = filters.assigned_to_user_id

        effective_filters = CustomerFilter(
            page=page,
            page_size=page_size,
            shop_id=filters.shop_id,
            status=filters.status,
            assigned_to_me=filters.assigned_to_me,
            assigned_to_user_id=effective_assigned_to_user_id,
            keyword=filters.keyword,
        )

        # 3. Repository に問い合わせ（DBアクセスはここから deeper 層）
        total_count, summaries = self.customer_query_repo.fetch_customer_summaries(
            current_user=current_user,
            filters=effective_filters,
            limit=page_size,
            offset=offset,
        )

        # 4. ReadModel に詰めて返す
        return CustomerListResult(
            total_count=total_count,
            page=page,
            page_size=page_size,
            customer_summaries=list(summaries),
        )
