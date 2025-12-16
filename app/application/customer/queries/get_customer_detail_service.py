from __future__ import annotations

from dataclasses import dataclass

from app.application.customer.read_models import CustomerDetailReadModel
from app.domain.user.models import User
from app.domain.user.errors import InactiveUserError
from app.application.customer.ports import CustomerQueryRepository
from app.application.common.errors import AuthorizationError, NotFoundError


@dataclass
class GetCustomerDetailQueryService:
    """顧客詳細など、読み取り系ユースケースを提供するサービス。"""

    customer_query_repo: CustomerQueryRepository

    def get_customer_detail(
        self,
        current_user: User,
        customer_id: int,
    ) -> CustomerDetailReadModel:
        """顧客詳細を取得するユースケース。
        - current_user が閲覧可能な顧客のみが対象
        - 顧客の基本情報に加え、最近の活動履歴・メモ・商談も含めて返す
        """
        # 1. 認可・前提条件チェック
        # ★ アクティブかどうかのルールはドメインに委譲する
        try:
            current_user.ensure_active()
        except InactiveUserError as exc:
            # 顧客閲覧というユースケースの文脈では
            # 「このユーザーはこの操作を行えない」という AuthorizationError にマッピング
            raise AuthorizationError("Inactive user") from exc

        # 2. Repository に問い合わせ（DBアクセスはここから deeper 層）
        detail = self.customer_query_repo.fetch_customer_detail(
            current_user=current_user,
            customer_id=customer_id,
        )

        # 3. fetch_customer_detail の戻り値は Optional[CustomerDetailReadModel] を想定
        if detail is None:
            # ユースケース上は「指定された顧客が見つからない」
            raise NotFoundError(f"Customer {customer_id} not found")

        # 3. ReadModel をそのまま返す（ここで __dict__ から作り直す必要はない）
        return detail
