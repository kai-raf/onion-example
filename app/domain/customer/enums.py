from enum import Enum


class CustomerStatus(str, Enum):
    """顧客のステータス。"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOST = "LOST"
