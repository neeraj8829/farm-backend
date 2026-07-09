import uuid
from datetime import date, datetime, timedelta, timezone


def new_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def date_offset(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def iter_date_range(check_in: str, check_out: str):
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)
    current = start
    while current < end:
        yield current.isoformat()
        current += timedelta(days=1)


def make_booking_id() -> str:
    return "BK-" + str(int(now_utc().timestamp()))[-5:] + "-" + uuid.uuid4().hex[:4].upper()

