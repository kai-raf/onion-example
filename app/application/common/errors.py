class AuthorizationError(Exception):
    """認可（アクセス権限）に関するアプリケーション例外。"""

    pass


class NotFoundError(Exception):
    """リソースが見つからない場合のアプリケーション例外。"""

    pass
