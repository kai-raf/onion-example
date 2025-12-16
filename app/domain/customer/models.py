from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.common.validators.email import validate_email
from app.domain.customer.enums import CustomerStatus
from app.domain.customer.errors import CustomerValidationError


@dataclass
class Customer:
    """ドメインモデルとしての顧客エンティティ"""

    id: Optional[int]
    shop_id: int
    email: str
    name: str
    status: CustomerStatus
    assigned_to_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        shop_id: int,
        email: str,
        name: str,
        assigned_to_user_id: Optional[int],
        status: Optional[CustomerStatus] = None,
    ) -> "Customer":
        """新規作成時の不変条件を満たした Customer を生成する。"""

        now = datetime.now(timezone.utc)

        # 1. 正規化
        email = (email or "").strip()
        name = (name or "").strip()

        # 2. 必須項目のバリデーション
        if not email:
            raise CustomerValidationError("email は必須です。")

        if not name:
            raise CustomerValidationError("name は必須です。")

        # 3. email 形式チェック（新規作成時も更新時も同じルールを適用したい）
        validate_email(email, exception_cls=CustomerValidationError)

        # 4. 初期ステータス
        if status is None:
            status = CustomerStatus.ACTIVE

        if status == CustomerStatus.LOST:
            raise CustomerValidationError("新規作成時に LOST ステータスは指定できません。")

        return cls(
            id=None,
            shop_id=shop_id,
            email=email,
            name=name,
            status=status,
            assigned_to_user_id=assigned_to_user_id,
            created_at=now,
            updated_at=now,
        )

    def _touch_updated_at(self, *, now: Optional[datetime] = None) -> None:
        self.updated_at = now or datetime.now(timezone.utc)

    def update_basic_info(
        self,
        *,
        name: Optional[str] = None,
        email: Optional[str] = None,
        assigned_to_user_id: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> None:
        """顧客の基本情報（名前・メール・担当者）を更新する。"""

        changed = False

        # name の更新
        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise CustomerValidationError("name は空文字にできません。")

            if normalized_name != self.name:
                self.name = normalized_name
                changed = True

        # email の更新
        if email is not None:
            normalized_email = email.strip()
            if not normalized_email:
                raise CustomerValidationError("email は空文字にできません。")

            validate_email(normalized_email, exception_cls=CustomerValidationError)

            if normalized_email != self.email:
                self.email = normalized_email
                changed = True

        # 担当者の更新
        if assigned_to_user_id is not None and assigned_to_user_id != self.assigned_to_user_id:
            self.assigned_to_user_id = assigned_to_user_id
            changed = True

        if changed:
            self._touch_updated_at(now=now)

    def change_status(
        self,
        new_status: CustomerStatus,
        *,
        now: Optional[datetime] = None,
    ) -> None:
        if new_status == self.status:
            return

        # 将来、ステータス遷移ルールをここに追加
        self.status = new_status
        self._touch_updated_at(now=now)
