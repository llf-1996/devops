"""时间工具。"""

from datetime import datetime
from zoneinfo import ZoneInfo

BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def get_now(tz: ZoneInfo = BEIJING_TZ) -> datetime:
    """返回指定时区的当前时间，默认北京时间。"""
    return datetime.now(tz)


def to_iso_string(value: datetime | None) -> str | None:
    """将 datetime 转为 ISO 8601 字符串；无时区信息时按北京时间处理。"""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=BEIJING_TZ)
    return value.isoformat()
