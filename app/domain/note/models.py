from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from datetime import datetime


@dataclass
class Note:
    """ドメインモデルとしての顧客に紐づくメモのエンティティ"""

    id: int
    customer_id: Optional[int]
    opportunity_id: Optional[int]
    body: str
    created_by_user_id: int
    created_at: datetime
