from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.customer.ports import ShopRepository
from app.infrastructure.orm.shop import ShopORM


class SqlAlchemyQueryShopRepository(ShopRepository):
    """ShopRepository の SQLAlchemy 実装。

    - 顧客作成などのユースケースから「shop が存在するかどうか」を確認するために利用する。
    - 責務は exists_by_id のみ（余計な取得ロジックは追加しない）。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def exists_by_id(self, shop_id: int) -> bool:
        """指定した shop_id を持つ店舗が存在するかを判定する。"""

        stmt = select(ShopORM.id).where(ShopORM.id == shop_id).limit(1)
        result = self._session.execute(stmt).scalar_one_or_none()

        # 行があれば True、なければ False
        return result is not None
