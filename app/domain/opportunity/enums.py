from enum import Enum


class OpportunityStatus(str, Enum):
    """商談の状態。"""

    OPEN = "OPEN"
    WON = "WON"
    LOST = "LOST"
    ON_HOLD = "ON_HOLD"
