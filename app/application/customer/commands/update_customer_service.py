# app/application/customer/commands/update_customer_service.py
from __future__ import annotations

from dataclasses import dataclass

from app.application.customer.command_inputs import UpdateCustomerInput
from app.application.customer.read_models import CustomerBasicReadModel
from app.application.customer.ports import CustomerRepository
from app.application.customer.errors import (
    DuplicateCustomerEmailError,
    InvalidCustomerInputError,
)
from app.application.common.errors import AuthorizationError, NotFoundError
from app.domain.customer.errors import CustomerValidationError
from app.domain.user.models import User
from app.domain.user.errors import InactiveUserError


@dataclass
class UpdateCustomerCommandService:
    """顧客の基本情報更新ユースケース（PATCH /api/customers/{customer_id}）"""

    customer_repo: CustomerRepository

    def update_customer(
        self,
        current_user: User,
        customer_id: int,
        data: UpdateCustomerInput,
    ) -> CustomerBasicReadModel:
        """顧客の基本情報を部分更新するユースケース。

        - current_user は必ずアクティブユーザーであること
        - 該当顧客が存在すること
        - email を変更する場合は同一 shop 内で重複していないこと
        - name / email のフォーマットや空文字禁止などはドメイン Customer が保証
        """

        # 1. 認可チェック（共通ルール：非アクティブユーザーは操作不可）
        try:
            current_user.ensure_active()
        except InactiveUserError as exc:
            raise AuthorizationError("Inactive user") from exc

        # 2. 対象顧客の取得
        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            # 「顧客が存在しない」というユースケースレベルのエラー
            raise NotFoundError(f"Customer {customer_id} not found")

        # 3. email を変更する場合のみ重複チェック
        if data.email is not None and data.email != customer.email:
            if self.customer_repo.exists_by_email(
                shop_id=customer.shop_id,
                email=data.email,
            ):
                raise DuplicateCustomerEmailError("email は既に使用されています。")

        # 4. ドメインロジックに更新を委譲
        try:
            # 名前 / メール / 担当者の更新（空文字禁止や email 形式チェックも含む）
            customer.update_basic_info(
                name=data.name,
                email=data.email,
                assigned_to_user_id=data.assigned_to_user_id,
            )

            # ステータス変更（必要なときだけ）
            if data.status is not None:
                customer.change_status(data.status)

        except CustomerValidationError as exc:
            # ドメインの検証エラーをアプリケーション層の入力エラーにマッピング
            raise InvalidCustomerInputError(str(exc)) from exc

        # 5. リポジトリで永続化
        saved = self.customer_repo.update(customer)

        # 6. ReadModel に詰め替えて返却
        return CustomerBasicReadModel(
            id=saved.id,
            shop_id=saved.shop_id,
            email=saved.email,
            name=saved.name,
            status=saved.status,
            assigned_to_user_id=saved.assigned_to_user_id,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
