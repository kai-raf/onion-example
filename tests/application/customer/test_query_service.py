from app.application.customer.queries.list_customers_service import ListCustomersQueryService
from app.application.customer.read_models import (
    CustomerSummaryReadModel,
    CustomerListResult,
)
from app.application.customer.query_filter import CustomerFilter
from app.domain.customer.enums import CustomerStatus
from app.domain.user.models import User


class InMemoryCustomerQueryRepo:
    """CustomerQueryRepository を模したテスト用のフェイク実装。"""

    def __init__(self, summaries):
        self._summaries = summaries

    def fetch_customer_summaries(self, current_user, filters, limit, offset):
        # 超シンプルに、渡された summaries をスライスして返す例
        total = len(self._summaries)
        return total, self._summaries[offset : offset + limit]


def test_list_customers_basic_pagination():
    # 準備：フェイクデータ
    user = User(
        id=1,
        email="taro@example.com",
        full_name="山田 太郎",
        hashed_password="x",
        is_active=True,
        is_superuser=False,
        timezone="Asia/Tokyo",
        roles=[],
        created_at="2025-01-04 10:00:00+09:00",
        updated_at="2025-01-04 10:00:00+09:00",
    )

    summaries = [
        CustomerSummaryReadModel(
            id=1,
            email="c1@example.com",
            name="顧客1",
            status=CustomerStatus.ACTIVE,
            shop_id=1,
            shop_name="渋谷店",
            assigned_to_user_id=1,
            assigned_to_user_name="山田 太郎",
            visit_count=3,
            last_visit_at=None,
            created_at="2025-01-01 10:00:00+09:00",
        ),
    ]

    repo = InMemoryCustomerQueryRepo(summaries)
    service = ListCustomersQueryService(customer_query_repo=repo)

    filters = CustomerFilter(page=1, page_size=10)

    result: CustomerListResult = service.list_customers(
        current_user=user,
        filters=filters,
    )

    assert result.total_count == len(summaries)
    assert len(result.customer_summaries) == len(summaries)
    assert result.page == 1
    assert result.page_size == 10
