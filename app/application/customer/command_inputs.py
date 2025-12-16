from typing import Optional
from app.domain.customer.enums import CustomerStatus

from dataclasses import dataclass

# 書き込み系ユースケースの「入力 DTO」をここに集約


@dataclass
class CreateCustomerInput:
    shop_id: int
    email: str
    name: str
    status: Optional[CustomerStatus] = None
    assigned_to_user_id: Optional[int] = None  # ★ これを追加


@dataclass
class UpdateCustomerInput:
    """顧客更新ユースケースの入力 DTO。

    - PATCH /api/customers/{customer_id} 用
    - None のフィールドは「今回のリクエストでは更新しない」と解釈する
    """

    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[CustomerStatus] = None
    assigned_to_user_id: Optional[int] = None
