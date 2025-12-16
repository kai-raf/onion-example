from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from decimal import Decimal

from datetime import datetime
from app.domain.opportunity.enums import OpportunityStatus


@dataclass
class OpportunityStage:
    id: int
    name: str
    display_order: int
    is_won: bool
    is_lost: bool


@dataclass
class Opportunity:
    id: int
    customer_id: int
    title: str
    amount: Optional[Decimal]
    probability: Optional[int]
    status: OpportunityStatus
    expected_close_date: Optional[datetime]
    stage: Optional[OpportunityStage]
    owner_user_id: int
    created_at: datetime
    updated_at: datetime
