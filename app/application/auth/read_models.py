from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)  # frozen=Trueでこのdataclass を不変（immutable）にする
class CurrentUserReadModel:
    """ログイン中ユーザーのプロフィール情報（/me 用のアプリケーション出力モデル）"""

    id: int
    email: str
    full_name: str
    roles: List[str]
    is_superuser: bool
