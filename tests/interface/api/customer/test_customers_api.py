from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.domain.user.models import User
from app.interface.api.auth.deps import get_current_user


# テスト用の current_user を差し込む
def override_get_current_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        hashed_password="dummy-hash",
        is_active=True,
        is_superuser=False,
        timezone="Asia/Tokyo",
        roles=[],  # 実際の User モデルに合わせて
        created_at=now,
        updated_at=now,
    )


app.dependency_overrides[get_current_user] = override_get_current_user


client = TestClient(app)


def test_get_customers_success():
    # 事前に dev.db に mock データを入れておく前提
    resp = client.get("/api/customers?page=1&page_size=20")
    assert resp.status_code == 200

    data = resp.json()
    assert "total_count" in data
    assert "customer_summaries" in data
    assert isinstance(data["customer_summaries"], list)
