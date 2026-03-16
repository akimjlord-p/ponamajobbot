from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def apptime():
    return datetime.now(ZoneInfo("Asia/Taipei"))