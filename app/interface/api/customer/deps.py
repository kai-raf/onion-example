from fastapi import Depends, Query
from sqlalchemy.orm import Session

from typing import Optional

from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.customer.customer_query_repository import (
    SqlAlchemyCustomerQueryRepository,
)
from app.infrastructure.repositories.customer.customer_command_repository import (
    SqlAlchemyCustomerCommandRepository,
)
from app.infrastructure.repositories.shop.shop_query_repository import (
    SqlAlchemyQueryShopRepository,
)

from app.application.customer.queries.get_customer_detail_service import GetCustomerDetailQueryService
from app.application.customer.queries.list_customers_service import ListCustomersQueryService
from app.application.customer.query_filter import CustomerFilter
from app.application.customer.commands.create_customer_service import CreateCustomerCommandService
from app.application.customer.commands.update_customer_service import UpdateCustomerCommandService

from app.domain.customer.enums import CustomerStatus


def get_customer_list_query_service(
    db: Session = Depends(get_db),
) -> ListCustomersQueryService:
    """
    FastAPI から DI するための CustomerQueryService ファクトリ。

    - SQLAlchemyCustomerQueryRepository(infrastructure) を注入した CustomerQueryService(application) を返す。
    """
    repo = SqlAlchemyCustomerQueryRepository(session=db)
    return ListCustomersQueryService(customer_query_repo=repo)


def get_customer_detail_query_service(
    db: Session = Depends(get_db),
) -> GetCustomerDetailQueryService:
    """
    FastAPI から DI するための CustomerQueryService ファクトリ。

    - SQLAlchemyCustomerQueryRepository(infrastructure) を注入した CustomerQueryService(application) を返す。
    """
    repo = SqlAlchemyCustomerQueryRepository(session=db)
    return GetCustomerDetailQueryService(customer_query_repo=repo)


def get_customer_list_filter(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CustomerStatus] = Query(
        None,
        description="顧客ステータスで絞り込み（ACTIVE / INACTIVE / LOST など）",
    ),
    shop_id: Optional[int] = Query(
        None,
        ge=1,
        description="店舗IDで絞り込み",
    ),
    assigned_to_me: bool = Query(
        False,
        description="true の場合、現在のログインユーザーが担当の顧客のみを表示",
    ),
    keyword: Optional[str] = Query(
        None,
        min_length=1,
        max_length=100,
        description="顧客名 / メールアドレスの部分一致検索",
    ),
) -> CustomerFilter:
    """顧客一覧用のクエリパラメータを CustomerFilter に詰める依存。"""

    return CustomerFilter(
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        status=status,
        assigned_to_me=assigned_to_me,
        # effective な担当者IDは application の Service で決めるのでここでは None
        assigned_to_user_id=None,
        keyword=keyword,
    )


# 顧客作成用の Service を組み立てる Depends
def get_create_customer_service(
    db: Session = Depends(get_db),
) -> CreateCustomerCommandService:
    """顧客作成ユースケース用の CreateCustomerService を組み立てる."""

    customer_repo = SqlAlchemyCustomerCommandRepository(db)
    shop_repo = SqlAlchemyQueryShopRepository(db)

    return CreateCustomerCommandService(
        customer_repo=customer_repo,
        shop_repo=shop_repo,
    )


# 顧客更新用の Service を組み立てる Depends
def get_update_customer_service(
    db: Session = Depends(get_db),
) -> UpdateCustomerCommandService:
    """顧客更新ユースケース用の UpdateCustomerCommandService を組み立てる."""

    customer_repo = SqlAlchemyCustomerCommandRepository(db)

    return UpdateCustomerCommandService(
        customer_repo=customer_repo,
    )
