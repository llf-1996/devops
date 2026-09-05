import logging
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import require_auth
from app.database import SessionLocal
from app.exceptions import exception_handler

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_exception_handler(Exception, exception_handler)

# 跨域白名单（禁止 * 与 credentials 同开）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admin.yaocai.co",
        "https://admin.test.yaocai.co",
        "https://y.yaocai.co",
        "https://y.test.yaocai.co",
    ],
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


def _persist_event(event: schemas.EventCreate) -> None:
    """后台落库：独立 Session，失败仅记日志（允许丢片）。"""
    db = SessionLocal()
    try:
        crud.create_event(db, event)
    except Exception:
        logger.exception(
            "rrweb 分片落库失败 request_id=%s seq=%s",
            event.request_id,
            event.seq,
        )
    finally:
        db.close()


@app.get("/ping")
def ping():
    """健康检查（无需鉴权），供容器探活使用。"""
    return {"status": "ok"}


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
    """录屏详情：按会话拉取分片；有 seq 按 seq，空则按 id。"""
    details = crud.get_event_details(db, request_id, company_id, user_id)
    return [schemas.EventDetailOut.model_validate(item) for item in details]


@app.post("/events", response_model=schemas.EventAcceptOut)
def create_event(
    event: schemas.EventCreate,
    background_tasks: BackgroundTasks,
    _auth: dict = Depends(require_auth),
):
    """
    上报受理：鉴权通过后入 BackgroundTasks 异步落库，立即返回 accepted。
    允许丢片；回放顺序依赖前端单调 seq。
    """
    background_tasks.add_task(_persist_event, event)
    return schemas.EventAcceptOut(status="accepted", request_id=event.request_id, seq=event.seq)
