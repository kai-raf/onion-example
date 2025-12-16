from app.infrastructure.db.base import Base

# ここで全 ORM を import して Base.metadata に登録させる
from app.infrastructure.orm.user import UserORM
from app.infrastructure.orm.role import RoleORM, UserRoleORM
from app.infrastructure.orm.shop import ShopORM
from app.infrastructure.orm.customer import CustomerORM
from app.infrastructure.orm.reservation import ReservationORM
from app.infrastructure.orm.activity import ActivityORM
from app.infrastructure.orm.opportunity import OpportunityORM, OpportunityStageORM
from app.infrastructure.orm.task import TaskORM
from app.infrastructure.orm.note import NoteORM
from app.infrastructure.orm.audit_log import AuditLogORM

__all__ = [
    "Base",
    "UserORM",
    "RoleORM",
    "UserRoleORM",
    "ShopORM",
    "CustomerORM",
    "ReservationORM",
    "ActivityORM",
    "OpportunityORM",
    "OpportunityStageORM",
    "TaskORM",
    "NoteORM",
    "AuditLogORM",
]
