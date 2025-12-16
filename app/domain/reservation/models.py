from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime

from typing import Optional

from app.domain.reservation.enums import ReservationStatus


@dataclass
class Reservation:
    """ドメインモデルとしての予約情報のエンティティ"""

    id: int
    shop_id: int
    customer_id: int
    status: ReservationStatus
    start_datetime: datetime
    end_datetime: datetime
    memo: Optional[str]
    created_at: datetime
    updated_at: datetime
