"""Clock seam so tests can freeze the Shanghai calendar day."""

from datetime import datetime
from zoneinfo import ZoneInfo


def now(tz: ZoneInfo) -> datetime:
    return datetime.now(tz)
