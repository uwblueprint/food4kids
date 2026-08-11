from datetime import datetime
from zoneinfo import ZoneInfo


def now_est_naive() -> datetime:
    """Current time in F4K's timezone (America/New_York), stored tz-naive."""
    return datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)
