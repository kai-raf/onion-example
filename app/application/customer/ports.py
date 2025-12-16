# app/application/customer/ports.py
# 1. 「ポート（ports.py）」の役割を一言でいうと
# application 層が「外に向けて要求する口（インターフェース）」です。
# 「こういう情報が欲しい」という要求（Port）は 内側（application/domain） が決める
# 「その情報をどう取ってくるか」（SQLAlchemyか、別サービスか、キャッシュか）は 外側（infrastructure） が決める

from __future__ import annotations

from typing import Protocol, Sequence, Optional

from app.application.customer.read_models import CustomerSummaryReadModel, CustomerDetailReadModel
from app.application.customer.query_filter import CustomerFilter
from app.domain.user.models import User
from app.domain.customer.models import Customer

"""
Title: 「application 層から 外の世界（DBなど）に向けて出す“要求の口（Port） を定義するファイル」

Description:
    「顧客一覧ユースケースとして、インフラにこういうことをしてほしい」という 契約だけ を定義。
    例：
      - current_user, filters, limit, offset を受け取って
      - total_count, customer_summaries を返すという宣言

Point:
    - 中身のロジックは書かない（Protocol インターフェースだけ）。
    - 実際の実装は infrastructure/repositories/customer_query_repository.py で行う。
    - 実際の処理を書かないことから以下が担保される
      - application は DB や SQLAlchemy を知らない
      - 「どうやって取ってくるか」はインフラが自由に変えられる
      - テストではフェイク実装を簡単に差し込める
    - オニオンアーキテクチャでいう 「Port」（口） がここ。
"""


class CustomerQueryRepository(Protocol):

    def fetch_customer_summaries(
        self,
        current_user: User,
        filters: CustomerFilter,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[CustomerSummaryReadModel]]:
        """顧客サマリー一覧を取得する。

        戻り値:
            total_count: フィルタ条件に一致する全件数
            customer_summaries: 現在ページに該当する顧客サマリーのリスト
        """
        ...

    def fetch_customer_detail(
        self,
        current_user: User,
        customer_id: int,
    ) -> Optional[CustomerDetailReadModel]:
        """顧客詳細を取得する。

        戻り値:
            CustomerDetailReadModel: 顧客詳細情報
        """
        ...


class CustomerRepository(Protocol):
    """顧客の書き込み系ユースケースで利用するリポジトリ（作成・更新など）。"""

    def exists_by_email(self, shop_id: int, email: str) -> bool:
        """指定した shop 内で email を持つ顧客が既に存在するかを判定する。"""
        ...

    def create(self, customer: Customer) -> Customer:
        """新規顧客を永続化する。

        引数:
            customer: ドメインの Customer エンティティ（id, created_at などは未確定の場合あり）

        戻り値:
            永続化後の Customer（id, created_at, updated_at などが確定した状態）
        """
        ...

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """ID で顧客を取得する。存在しなければ None."""
        ...

    def update(self, customer: Customer) -> Customer:
        """顧客情報を更新し、更新後の Customer を返す."""
        ...


class ShopRepository(Protocol):
    """顧客作成時などに、店舗の存在を確認するためのリポジトリ。"""

    def exists_by_id(self, shop_id: int) -> bool:
        """指定した shop_id を持つ店舗が存在するかを判定する。"""
        ...
