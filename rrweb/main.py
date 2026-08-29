from typing import List, Optional

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import require_auth
from app.database import SessionLocal
from app.exceptions import exception_handler

app = FastAPI()
app.add_exception_handler(Exception, exception_handler)

# 允许所有跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/events", response_model=schemas.EventListResponse)
def list_events(
    page: int = 1,
    page_size: int = 20,
    company_id: Optional[int] = Query(None, description="公司ID，精确匹配"),
    user_id: Optional[int] = Query(None, description="用户ID，精确匹配"),
    order_plan_id: Optional[int] = Query(
        None, description="采购订单ID，精确匹配 payload.order_plan_id"
    ),
    company_name: Optional[str] = Query(None, description="公司名，模糊匹配"),
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """录屏列表：查会话表，按 updated_at 降序；支持公司/用户/订单精确筛选与公司名模糊筛选。"""
    skip = (page - 1) * page_size
    count, results = crud.get_events(
        db,
        skip=skip,
        limit=page_size,
        company_id=company_id,
        user_id=user_id,
        company_name=company_name,
        order_plan_id=order_plan_id,
    )
    results_out = [schemas.EventListOut.model_validate(r) for r in results]
    return schemas.EventListResponse(count=count, results=results_out)


@app.get("/events/detail", response_model=List[schemas.EventDetailOut])
def get_event(
    request_id: str,
    company_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """录屏详情：按会话拉取分片，按 id 升序。"""
    details = crud.get_event_details(db, request_id, company_id, user_id)
    return [schemas.EventDetailOut.model_validate(item) for item in details]


@app.post("/events", response_model=schemas.EventListOut)
def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """上报：upsert 会话并插入事件分片。"""
    ins_session = crud.create_event(db, event)
    return schemas.EventListOut.model_validate(ins_session)
