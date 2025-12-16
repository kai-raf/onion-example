from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from datetime import datetime

from app.domain.activity.enums import ActivityType


@dataclass
class Activity:
    """ドメインモデルとしての活動履歴エンティティ"""

    id: int
    customer_id: Optional[int]
    type: ActivityType
    subject: str
    description: Optional[str]
    scheduled_at: Optional[datetime]
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
