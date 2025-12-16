# app/application/auth/services.py
from __future__ import annotations

from dataclasses import dataclass

from app.domain.user.models import User
from app.domain.user.errors import InactiveUserError
from app.domain.auth.models import AuthToken

from app.application.auth.ports import UserRepository, PasswordHasher, TokenProvider
from app.application.auth.read_models import CurrentUserReadModel


class AuthenticationError(Exception):
    """認証失敗（メール or パスワード不正・非アクティブユーザーなど）の例外"""

    pass


class TokenError(Exception):
    """トークンの検証失敗（不正 / 期限切れなど）の例外"""

    pass


@dataclass(frozen=True)
class AuthSettings:
    """認証関連の設定値（settings から注入する想定）"""

    access_token_expires_minutes: int


"""
 「AuthService は、ログイン や トークンからユーザーを特定する といった
  認証に関する仕事の一連の流れ” をまとめて担当するクラス」
"""


class AuthService:
    """認証ユースケースを担当するアプリケーションサービス"""

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_provider: TokenProvider,
        settings: AuthSettings,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._token_provider = token_provider
        self._settings = settings

    # ==========
    # ログイン
    # ==========

    def authenticate(self, email: str, password: str) -> User:
        """
        メールアドレスとパスワードで認証し、User を返す。

        失敗した場合は AuthenticationError を送出する。
        """

        user = self._user_repo.get_by_email(email)
        if user is None:
            # メッセージはあえてぼかす（emailかpasswordか分からないように）
            raise AuthenticationError("Invalid email or password")

        if not self._password_hasher.verify(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Inactive user")

        return user

    # ==========
    # アクセストークン発行
    # ==========

    def create_access_token(self, user: User) -> AuthToken:
        """
        指定ユーザーのアクセストークンを発行する。

        payload の構造（"sub" に何を入れるかなど）は infra 側の JwtTokenProvider と合わせる。
        """

        payload = {
            "sub": str(user.id),
            "email": user.email,
            # 必要に応じて is_superuser や roles も含めてOK
        }

        token_str = self._token_provider.encode(
            payload=payload,
            expires_in_minutes=self._settings.access_token_expires_minutes,
        )

        return AuthToken(access_token=token_str, token_type="bearer")

    # ===================
    # トークンからユーザーを復元する
    # ===================

    def get_user_from_token(self, token: str) -> User:
        """
        アクセストークンから User を取得する。

        - トークン不正 / 期限切れ → TokenError
        - User が存在しない / 非アクティブ → AuthenticationError
        """

        try:
            payload = self._token_provider.decode(token)
        except Exception as e:
            # 実際には infra 側で専用例外を投げて、それをここで捕まえてもよい
            raise TokenError("Invalid token") from e

        sub = payload.get("sub")
        if sub is None:
            raise TokenError("Token payload missing 'sub'")

        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise TokenError("Token 'sub' must be an integer string")

        user = self._user_repo.get_by_id(user_id)
        # ★ アクティブかどうかのルールはドメインに委譲する
        try:
            user.ensure_active()
        except InactiveUserError as exc:
            # 「ログイン」というユースケースの文脈では
            # ドメインの InactiveUserError を「認証失敗」として扱う
            raise AuthenticationError("Inactive user") from exc

        return user

    # =============================
    # /me 用の ReadModel 生成ヘルパー
    # =============================

    def build_current_user_read_model(self, user: User) -> CurrentUserReadModel:
        """
        domain.User から /me 用の CurrentUserReadModel を組み立てる。
        """

        # full_name の作り方は domain.User の設計に合わせて調整してください。
        # 例: name_sei + name_mei を join する、full_name プロパティをそのまま使う、など。
        full_name = getattr(user, "full_name", user.email)  # 仮の実装

        # user.roles が List[Role] を持っている想定。
        roles = [role.name for role in getattr(user, "roles", [])]

        return CurrentUserReadModel(
            id=user.id,
            email=user.email,
            full_name=full_name,
            roles=roles,
            is_superuser=user.is_superuser,
        )
