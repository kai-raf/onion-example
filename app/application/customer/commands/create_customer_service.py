# app/application/customer/query_service.py
from __future__ import annotations

from dataclasses import dataclass

from app.application.customer.read_models import CustomerBasicReadModel
from app.domain.user.models import User
from app.application.customer.ports import CustomerRepository, ShopRepository
from app.application.customer.errors import ShopNotFoundError, DuplicateCustomerEmailError, InvalidCustomerInputError
from app.domain.customer.models import Customer
from app.domain.customer.errors import CustomerValidationError
from app.application.customer.command_inputs import CreateCustomerInput
from app.domain.user.errors import InactiveUserError
from app.application.common.errors import AuthorizationError, NotFoundError

"""
Title: 「顧客作成ユースケースそのもの（処理の本体）を書くファイル」
"""


@dataclass
class CreateCustomerCommandService:
    customer_repo: CustomerRepository
    shop_repo: ShopRepository

    def create_customer(
        self,
        current_user: User,
        data: CreateCustomerInput,
    ) -> CustomerBasicReadModel:
        """新規顧客を作成するユースケース。"""

        # 認可チェック（共通ルール：非アクティブユーザーは操作不可）
        try:
            current_user.ensure_active()
        except InactiveUserError as exc:
            raise AuthorizationError("Inactive user") from exc

        # 1. shop の存在チェック
        if not self.shop_repo.exists_by_id(data.shop_id):
            raise ShopNotFoundError(f"Shop not found: id={data.shop_id}")

        # 2. email 重複チェック
        if self.customer_repo.exists_by_email(shop_id=data.shop_id, email=data.email):
            raise DuplicateCustomerEmailError(f"Customer with email already exists: {data.email}")

        # 3. ドメインルールに従って Customer を生成
        try:
            customer = Customer.create(
                shop_id=data.shop_id,
                email=data.email,
                name=data.name,
                assigned_to_user_id=current_user.id,
                status=data.status,
            )
        except CustomerValidationError as exc:
            raise InvalidCustomerInputError(str(exc)) from exc

        # 4. 永続化
        saved = self.customer_repo.create(customer)
        # ↑ ここで saved.id / saved.created_at / saved.updated_at などが埋まっている前提

        # 5. Application の ReadModel に変換して返す
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
