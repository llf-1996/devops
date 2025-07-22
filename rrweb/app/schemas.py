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


class EventCreate(BaseModel):
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    events: List[Any]
    payload: Optional[dict] = dict()
    request_id: Optional[str] = None
    request_at: datetime


class EventListOut(BaseModel):
    id: int
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    payload: Optional[dict] = dict()
    request_id: Optional[str] = None
    request_at: datetime

    class Config:
        from_attributes = True


class EventDetailOut(BaseModel):
    id: int
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    events: List[Any]
    payload: Optional[dict] = dict()
    request_id: Optional[str] = None
    request_at: datetime

    class Config:
        from_attributes = True
