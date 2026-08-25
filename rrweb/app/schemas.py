from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


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


class EventListOut(BaseModel):
    """录屏列出会话项。"""

    id: int
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    payload: Optional[dict] = Field(default_factory=dict)
    request_id: Optional[str] = None
    record_type: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EventDetailOut(BaseModel):
    """录屏详情分片项（回放按 id 升序拼接 events）。"""

    id: int
    session_id: int
    events: List[Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
