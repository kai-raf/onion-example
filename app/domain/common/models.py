from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TimestampedEntity:
    created_at: datetime
    updated_at: datetime

    def touch(self, now: datetime | None = None) -> None:
        self.updated_at = now or utc_now()
