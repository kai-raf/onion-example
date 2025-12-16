from dataclasses import dataclass
from typing import Optional

from app.domain.customer.enums import CustomerStatus

"""
Title: 「顧客一覧ユースケースの “入力条件（フィルタ）” を定義するファイル」

Description:
    ユースケースの「入口」を表す。

    例：
      - CustomerFilter
      - page, page_size
      - status
      - shop_id
      - keyword
    など「どんな顧客一覧が欲しいか」の条件をまとめたモデル。

Point:
    - 中身は dataclass だけ（ロジックは書かない）。
    - FastAPI が受け取った query パラメータを、最終的にこの CustomerFilter に詰めて CustomerQueryService に渡すイメージ。
    - 「HTTPのクエリ文字列 → CustomerFilter」という変換は interface 層が担当し、application 層では CustomerFilter だけを扱う。
"""


@dataclass
class CustomerFilter:
    """顧客検索条件"""

    page: Optional[int] = 1
    page_size: Optional[int] = 20
    shop_id: Optional[int] = None
    status: Optional[CustomerStatus] = None
    assigned_to_me: bool = False
    assigned_to_user_id: Optional[int] = None
    keyword: Optional[str] = None
