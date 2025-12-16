from enum import Enum


class OpportunityStatus(str, Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    ON_HOLD = "on_hold"
