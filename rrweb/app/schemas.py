from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class EventBase(BaseModel):
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    events: List[Any]
    payload: Optional[dict] = dict()
    request_id: Optional[str] = None


class EventCreate(EventBase):
    request_at: datetime


class EventOut(EventBase):
    id: int
    request_at: datetime

    class Config:
        from_attributes = True
