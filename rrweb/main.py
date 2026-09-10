import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.auth import close_verify_client, require_auth
from app.database import AsyncSessionLocal, engine
from app.exceptions import exception_handler, http_exception_handler
from app.utils.datetime_utils import get_now

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期：退出时释放鉴权客户端与数据库连接池。"""
    yield
    await close_verify_client()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(HTTPException, http_exception_handler)
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


async def get_db():
    """请求级异步数据库会话。"""
    async with AsyncSessionLocal() as db:
        yield db


async def _persist_event(event: schemas.EventCreate) -> None:
    """后台落库：独立 Session，失败仅记日志（允许丢片）。"""
    try:
        async with AsyncSessionLocal() as db:
            await crud.create_event(db, event)
    except Exception:
        logger.exception(
            "rrweb 分片落库失败 request_id=%s seq=%s",
            event.request_id,
            event.seq,
        )


async def _cleanup_unlocked_sessions(cutoff_naive: datetime) -> None:
    """后台清理：独立 Session，失败仅记日志。"""
    try:
        async with AsyncSessionLocal() as db:
            deleted_count = await crud.cleanup_unlocked_sessions(db, cutoff_naive)
        logger.info("rrweb 清理完成 deleted_count=%s cutoff=%s", deleted_count, cutoff_naive)
    except Exception:
        logger.exception("rrweb 清理失败 cutoff=%s", cutoff_naive)


@app.get("/ping")
async def ping():
    """健康检查（无需鉴权），供容器探活使用。"""
    return {"status": "ok"}


@app.get("/events", response_model=schemas.EventListResponse)
async def list_events(
    page: int = 1,
    page_size: int = 20,
    company_id: Optional[int] = Query(None, description="公司ID，精确匹配"),
    user_id: Optional[int] = Query(None, description="用户ID，精确匹配"),
    order_plan_id: Optional[int] = Query(
        None, description="采购订单ID，精确匹配 payload.order_plan_id"
    ),
    company_name: Optional[str] = Query(None, description="公司名，模糊匹配"),
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """录屏列表：查会话表，按 updated_at 降序；支持公司/用户/订单精确筛选与公司名模糊筛选。"""
    skip = (page - 1) * page_size
    count, results = await crud.get_events(
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
async def get_event(
    request_id: str,
    company_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """录屏详情：按会话拉取分片；有 seq 按 seq，空则按 id。"""
    details = await crud.get_event_details(db, request_id, company_id, user_id)
    return [schemas.EventDetailOut.model_validate(item) for item in details]


@app.post("/events", response_model=schemas.EventAcceptOut)
async def create_event(
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


@app.patch("/events/{session_id}/lock", response_model=schemas.SessionLockOut)
async def lock_session(
    session_id: int,
    body: schemas.SessionLockIn,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """锁定或解锁录屏会话；锁定后不可删除、不可被清理。"""
    try:
        ins_session = await crud.set_session_locked(db, session_id, body.is_locked)
    except crud.SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return schemas.SessionLockOut(id=ins_session.id, is_locked=ins_session.is_locked)


@app.delete("/events/{session_id}", response_model=schemas.SessionDeleteOut)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: dict = Depends(require_auth),
):
    """删除单个录屏会话及其分片；已锁定则拒绝。"""
    try:
        deleted_id = await crud.delete_session(db, session_id)
    except crud.SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except crud.SessionLockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schemas.SessionDeleteOut(id=deleted_id, status="deleted")


@app.post("/events/cleanup", response_model=schemas.CleanupOut)
async def cleanup_events(
    background_tasks: BackgroundTasks,
    _auth: dict = Depends(require_auth),
):
    """
    清理受理：鉴权通过后入 BackgroundTasks 异步清理 6 个月以前且未锁定的会话。
    已锁定保留；立即返回 accepted。
    """
    cutoff_at = get_now() - timedelta(days=30 * 6)
    # MySQL DATETIME 常为无时区；与库内 naive 比较时去掉 tzinfo
    cutoff_naive = cutoff_at.replace(tzinfo=None)
    background_tasks.add_task(_cleanup_unlocked_sessions, cutoff_naive)
    return schemas.CleanupOut(status="accepted", cutoff_at=cutoff_at)
