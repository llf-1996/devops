from datetime import datetime
from typing import Annotated, Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from app.utils.datetime_utils import to_iso_string

ISODatetime = Annotated[
    Optional[datetime],
    PlainSerializer(to_iso_string, return_type=Optional[str]),
]


class AppSchemaBase(BaseModel):
    """响应 Schema 基类：支持 ORM 对象转换。"""

    model_config = ConfigDict(from_attributes=True)


class EventCreate(BaseModel):
    """录屏上报请求体。"""

    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    events: List[Any]
    payload: Optional[dict] = Field(default_factory=dict)
    request_id: str
    record_type: int = 1
    seq: Optional[int] = Field(default=None, description="同一会话内分片序号，前端单调递增")


class EventAcceptOut(AppSchemaBase):
    """录屏上报受理响应（BackgroundTasks 异步落库）。"""

    status: str = "accepted"
    request_id: str
    seq: Optional[int] = None


class EventListOut(AppSchemaBase):
    """录屏列出会话项。"""

    id: int
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    payload: Optional[dict] = Field(default_factory=dict)
    request_id: Optional[str] = None
    record_type: int = 1
    is_locked: int = 0
    created_at: ISODatetime = None
    updated_at: ISODatetime = None


class SessionLockIn(BaseModel):
    """会话锁定状态更新请求体。"""

    is_locked: bool = Field(..., description="true=锁定，false=解锁")


class SessionLockOut(AppSchemaBase):
    """会话锁定状态更新响应。"""

    id: int
    is_locked: int


class SessionDeleteOut(AppSchemaBase):
    """会话删除响应。"""

    id: int
    status: str = "deleted"


class CleanupOut(AppSchemaBase):
    """清理受理响应（BackgroundTasks 异步执行）。"""

    status: str = "accepted"
    cutoff_at: ISODatetime = None


class EventDetailOut(AppSchemaBase):
    """录屏详情分片项（回放优先按 seq，空则按 id）。"""

    id: int
    session_id: int
    seq: Optional[int] = None
    events: List[Any]
    created_at: ISODatetime = None
    updated_at: ISODatetime = None


class EventListResponse(AppSchemaBase):
    """录屏列表响应。"""

    count: int
    results: List[EventListOut]
