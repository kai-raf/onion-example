# tests/infrastructure/customer/test_sqlalchemy_customer_query_repository.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.infrastructure.orm import (
    Base,
    UserORM,
    ShopORM,
    CustomerORM,
    ReservationORM,
)
from app.infrastructure.repositories.customer.customer_query_repository import (
    SqlAlchemyCustomerQueryRepository,
)
from app.domain.customer.enums import CustomerStatus
from app.domain.user.models import User
from app.domain.reservation.enums import ReservationStatus
from app.application.customer.query_filter import CustomerFilter


# =========================
# テスト用 DB / Session の fixture
# =========================


@pytest.fixture(scope="session")
def engine():
    """テスト用の SQLite in-memory エンジンを作成."""
    engine = create_engine("sqlite:///:memory:", future=True)
    # テーブルを一括作成
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def session(engine) -> Generator[Session, None, None]:
    """テストごとに新しい Session を提供."""
    with engine.connect() as connection:
        # テストごとにトランザクションを張って、最後にロールバックするパターンでもOK
        trans = connection.begin()
        session = Session(bind=connection)

        try:
            yield session
        finally:
            session.close()
            trans.rollback()  # テストの変更を毎回巻き戻す


# =========================
# テストデータ投入用ヘルパー
# =========================


def _insert_sample_data(session: Session) -> User:
    """ユーザー / 店舗 / 顧客 / 予約のサンプルデータを投入し、
    current_user として使う User ドメインモデルを返す。
    """
    now = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    # --- User 作成 ---
    user_orm = UserORM(
        email="taro@example.com",
        full_name="山田 太郎",
        hashed_password="dummy-hash",
        is_active=True,
        is_superuser=False,
        timezone="Asia/Tokyo",
        created_at=now,
        updated_at=now,
        version=1,
    )
    session.add(user_orm)
    session.flush()  # id を採番させる

    # --- Shop 作成 ---
    shop1 = ShopORM(
        code="SHOP-A",
        name="渋谷店",
        address="東京都渋谷区1-1-1",
        phone_number="03-1111-1111",
        status="ACTIVE",  # Enum を文字列で持っている場合
        owner_user_id=user_orm.id,
        created_at=now,
        updated_at=now,
        version=1,
    )
    shop2 = ShopORM(
        code="SHOP-B",
        name="新宿店",
        address="東京都新宿区2-2-2",
        phone_number="03-2222-2222",
        status="ACTIVE",
        owner_user_id=user_orm.id,
        created_at=now,
        updated_at=now,
        version=1,
    )
    session.add_all([shop1, shop2])
    session.flush()

    # --- Customer 作成 ---
    customer1 = CustomerORM(
        shop_id=shop1.id,
        external_code=None,
        name="佐々木 一郎",
        email="customer1@example.com",
        phone_number=None,
        status=CustomerStatus.ACTIVE,  # Enum 型で代入OK
        rank=None,
        assigned_to_user_id=user_orm.id,
        created_at=now,
        updated_at=now,
        version=1,
    )
    customer2 = CustomerORM(
        shop_id=shop1.id,
        external_code=None,
        name="田中 二郎",
        email="customer2@example.com",
        phone_number=None,
        status=CustomerStatus.ACTIVE,
        rank=None,
        assigned_to_user_id=user_orm.id,
        created_at=now,
        updated_at=now,
        version=1,
    )
    customer3 = CustomerORM(
        shop_id=shop2.id,
        external_code=None,
        name="鈴木 三郎",
        email="customer3@example.com",
        phone_number=None,
        status=CustomerStatus.INACTIVE,
        rank=None,
        assigned_to_user_id=None,
        created_at=now,
        updated_at=now,
        version=1,
    )
    session.add_all([customer1, customer2, customer3])
    session.flush()

    # --- Reservation 作成 ---
    # customer1: 予約3件
    r1 = ReservationORM(
        shop_id=shop1.id,
        customer_id=customer1.id,
        status=ReservationStatus.PAID,
        start_datetime=datetime(2025, 1, 10, 10, 0, tzinfo=timezone.utc),
        end_datetime=datetime(2025, 1, 10, 11, 0, tzinfo=timezone.utc),
        memo="初回来店・成約",
        created_at=now,
        updated_at=now,
        version=1,
    )
    r2 = ReservationORM(
        shop_id=shop1.id,
        customer_id=customer1.id,
        status=ReservationStatus.VISITED,
        start_datetime=datetime(2025, 2, 1, 14, 0, tzinfo=timezone.utc),
        end_datetime=datetime(2025, 2, 1, 15, 0, tzinfo=timezone.utc),
        memo="定期フォロー",
        created_at=now,
        updated_at=now,
        version=1,
    )
    r3 = ReservationORM(
        shop_id=shop1.id,
        customer_id=customer1.id,
        status=ReservationStatus.BEFORE_VISIT,
        start_datetime=datetime(2025, 3, 5, 16, 0, tzinfo=timezone.utc),
        end_datetime=datetime(2025, 3, 5, 17, 0, tzinfo=timezone.utc),
        memo="次回アポ",
        created_at=now,
        updated_at=now,
        version=1,
    )
    # customer2: 予約1件（キャンセル）
    r4 = ReservationORM(
        shop_id=shop1.id,
        customer_id=customer2.id,
        status=ReservationStatus.CANCELED,
        start_datetime=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        end_datetime=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc),
        memo="当日キャンセル",
        created_at=now,
        updated_at=now,
        version=1,
    )
    session.add_all([r1, r2, r3, r4])
    session.commit()

    # application 層で使う User ドメインモデルを返す
    current_user = User(
        id=user_orm.id,
        email=user_orm.email,
        full_name=user_orm.full_name,
        hashed_password=user_orm.hashed_password,
        is_active=user_orm.is_active,
        is_superuser=user_orm.is_superuser,
        timezone=user_orm.timezone,
        roles=[],
        created_at=user_orm.created_at,
        updated_at=user_orm.updated_at,
    )
    return current_user


# =========================
# 実際のリポジトリのテスト
# =========================


def test_fetch_customer_summaries_basic(session: Session):
    """基本的な顧客サマリ一覧が取得できることのテスト。"""
    current_user = _insert_sample_data(session)

    repo = SqlAlchemyCustomerQueryRepository(session=session)

    # フィルタ：1ページ目、ページサイズ100（実質全件）
    filters = CustomerFilter(
        page=1,
        page_size=100,
        status=None,
        keyword=None,
        shop_id=None,
        assigned_to_user_id=None,
    )

    total_count, items = repo.fetch_customer_summaries(
        current_user=current_user,
        filters=filters,
        limit=filters.page_size,
        offset=0,
    )

    # --- 件数チェック ---
    assert total_count == 3
    assert len(items) == 3

    # 顧客1の visit_count / last_visit_at が期待通りか
    c1 = next(c for c in items if c.email == "customer1@example.com")
    assert c1.visit_count == 3
    # 最終来店日時が r3.start_datetime と一致しているか（あなたの実装に合わせて）
    assert c1.last_visit_at.year == 2025
    assert c1.last_visit_at.month == 3

    # 顧客3が shop2（新宿店）に紐づいているか
    c3 = next(c for c in items if c.email == "customer3@example.com")
    assert c3.shop_name == "新宿店"


def test_fetch_customer_summaries_filter_by_status(session: Session):
    """ステータスでフィルタできることのテスト。"""
    current_user = _insert_sample_data(session)
    repo = SqlAlchemyCustomerQueryRepository(session=session)

    # ACTIVE のみ
    filters = CustomerFilter(
        page=1,
        page_size=100,
        status=CustomerStatus.ACTIVE,
        keyword=None,
        shop_id=None,
        assigned_to_user_id=None,
    )

    total_count, items = repo.fetch_customer_summaries(
        current_user=current_user,
        filters=filters,
        limit=filters.page_size,
        offset=0,
    )

    # ACTIVE は 2 件（customer1, customer2）
    assert total_count == 2
    emails = {c.email for c in items}
    assert emails == {"customer1@example.com", "customer2@example.com"}
