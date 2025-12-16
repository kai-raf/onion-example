# app/infrastructure/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """全 ORM モデルのベースクラス。"""

    pass
