# =========================
# アプリケーション層の例外
# =========================


class ShopNotFoundError(Exception):
    """指定された shop_id に対応する店舗が存在しない。"""

    pass


class DuplicateCustomerEmailError(Exception):
    """同じ email を持つ顧客がすでに存在する。"""

    pass


class InvalidCustomerInputError(Exception):
    """ドメインのバリデーションに反した入力（HTTP 400 相当）。"""

    pass
