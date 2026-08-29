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
    created_at: ISODatetime = None
    updated_at: ISODatetime = None


class EventDetailOut(AppSchemaBase):
    """录屏详情分片项（回放按 id 升序拼接 events）。"""

    id: int
    session_id: int
    events: List[Any]
    created_at: ISODatetime = None
    updated_at: ISODatetime = None


class EventListResponse(AppSchemaBase):
    """录屏列表响应。"""

    count: int
    results: List[EventListOut]
