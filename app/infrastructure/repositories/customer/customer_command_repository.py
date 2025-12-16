# app/infrastructure/repositories/customer/customer_command_repository.py
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.customer.ports import CustomerRepository  # ← ports.py の名前に合わせる
from app.domain.customer.models import Customer
from app.infrastructure.orm.customer import CustomerORM


class SqlAlchemyCustomerCommandRepository(CustomerRepository):
    """顧客の作成・更新など、書き込み系ユースケース用の SQLAlchemy 実装。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    # -----------------------------
    # 既存: メール重複チェック
    # -----------------------------
    def exists_by_email(self, shop_id: int, email: str) -> bool:
        stmt = (
            select(CustomerORM.id)
            .where(
                CustomerORM.shop_id == shop_id,
                CustomerORM.email == email,
            )
            .limit(1)
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return result is not None

    # -----------------------------
    # 既存: 作成（create）
    # -----------------------------
    def create(self, customer: Customer) -> Customer:
        """新規顧客を永続化して、保存後の Customer を返す。"""

        orm = CustomerORM(
            shop_id=customer.shop_id,
            external_code=None,  # 必要になれば Input から渡す
            name=customer.name,
            email=customer.email,
            phone_number=None,  # 必要になれば Input から渡す
            status=customer.status,
            rank=None,
            assigned_to_user_id=customer.assigned_to_user_id,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            # version は ORM 側の default=1 に任せる
        )

        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)

        return self._to_domain_customer(orm)

    # -----------------------------
    # 追加: ID で顧客取得
    # -----------------------------
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """ID で顧客を取得する。存在しなければ None。"""
        orm = self._session.get(CustomerORM, customer_id)
        if orm is None:
            return None
        return self._to_domain_customer(orm)

    # -----------------------------
    # 追加: 顧客更新
    # -----------------------------
    def update(self, customer: Customer) -> Customer:
        """顧客情報を更新し、更新後の Customer を返す。"""

        if customer.id is None:
            # 更新ユースケースで id=None は設計ミスなので、はっきり落とす
            raise RuntimeError("update() called with Customer.id=None")

        orm = self._session.get(CustomerORM, customer.id)
        if orm is None:
            # ここに来る前に application 層で NotFoundError を投げている前提なので、
            # 実際に None だった場合はプログラミングエラー扱い
            raise RuntimeError(f"Customer(id={customer.id}) not found in update().")

        # domain Customer の状態を ORM に反映
        orm.name = customer.name
        orm.email = customer.email
        orm.status = customer.status
        orm.assigned_to_user_id = customer.assigned_to_user_id
        orm.updated_at = customer.updated_at

        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)

        return self._to_domain_customer(orm)

    # -----------------------------
    # 共通: ORM → Domain 変換
    # -----------------------------
    def _to_domain_customer(self, orm: CustomerORM) -> Customer:
        """ORM からドメイン Customer への変換."""
        return Customer(
            id=orm.id,
            shop_id=orm.shop_id,
            email=orm.email,
            name=orm.name,
            status=orm.status,
            assigned_to_user_id=orm.assigned_to_user_id,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
