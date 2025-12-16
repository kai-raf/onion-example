from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime

from app.domain.shop.enums import ShopStatus


@dataclass
class Shop:
    """ドメインモデルとしての店舗エンティティ"""

    id: int
    code: str
    name: str
    address: str
    phone_number: str
    status: ShopStatus
    created_at: datetime
    updated_at: datetime
