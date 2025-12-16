from enum import IntEnum

class ReservationStatus(IntEnum):
    """予約 / 来店ステータス。"""
    BEFORE_VISIT = 1   # 来店前
    VISITED = 2        # 来店済み
    PAID = 3           # 会計済み
    CANCELED = 4       # キャンセル
