from enum import Enum


class ActivityType(str, Enum):
    CALL = "CALL"
    VISIT = "VISIT"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    OTHER = "OTHER"
