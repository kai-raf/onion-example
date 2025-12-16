from enum import Enum


class UserRoleName(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"
