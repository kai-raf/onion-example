from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

"""
①リクエスト到着
②FastAPI が Depends(get_db) を評価 → db = SessionLocal() で Session 作成
③yield db で一旦中断し、エンドポイント関数（router）が実行される
  - この中で CustomerCommandService.create_customer → CustomerRepository.create が呼ばれる
  - その中で add / flush / refresh が動く
④エンドポイント関数が正常に戻る（レスポンス用オブジェクトを返す）
⑤get_db の yield の後ろに処理が戻る → db.commit() 実行
  - ここで初めて「このリクエスト内の INSERT/UPDATE/DELETE が確定」する
⑥finally で db.close()、接続クローズ
⑦レスポンスがクライアントに返る
  - もし 3〜4 のどこかで例外が起きたら：
  - yield の後ろの db.commit() には到達せず、except に飛んで db.rollback()
  - そのリクエスト中の変更はすべて取り消される
"""

DATABASE_URL = settings.database_url


def _create_engine(url: str):
    if url.startswith("sqlite://"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            future=True,
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        future=True,
    )


engine = _create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends 用の DB セッション依存関数。

    - 1 リクエスト = 1 トランザクション
    - 正常終了時: commit
    - 例外発生時: rollback
    """
    db: Session = SessionLocal()
    try:
        yield db  # ★ ここでルーター / service / repository が実行される
        db.commit()  # ★ 正常終了ならここでトランザクション確定
    except Exception:
        db.rollback()  # ★ 何か例外が出たらすべて取り消し
        raise
    finally:
        db.close()
