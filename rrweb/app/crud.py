from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models, schemas
from .utils.datetime_utils import get_now


def get_event_details(
    db: Session, request_id: str, company_id: int, user_id: int
) -> List[models.RrwebEventDetail]:
    """按会话定位后，按 id 升序返回事件分片。"""
    ins_session = (
        db.query(models.RrwebSession)
        .filter(
            models.RrwebSession.request_id == request_id,
            models.RrwebSession.company_id == company_id,
            models.RrwebSession.user_id == user_id,
        )
        .first()
    )
    if not ins_session:
        return []
    return (
        db.query(models.RrwebEventDetail)
        .filter(models.RrwebEventDetail.session_id == ins_session.id)
        .order_by(models.RrwebEventDetail.id.asc())
        .all()
    )


def _apply_list_filters(
    query,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
    company_name: Optional[str] = None,
    order_plan_id: Optional[int] = None,
):
    """为录屏列表查询追加可选筛选条件。"""
    if company_id is not None:
        query = query.filter(models.RrwebSession.company_id == company_id)
    if user_id is not None:
        query = query.filter(models.RrwebSession.user_id == user_id)
    if company_name:
        query = query.filter(models.RrwebSession.company_name.like(f"%{company_name}%"))
    if order_plan_id is not None:
        # payload.order_plan_id 可能为数字或字符串，两种写法都匹配
        order_plan_id_str = str(order_plan_id)
        query = query.filter(
            or_(
                models.RrwebSession.payload["order_plan_id"].as_integer() == order_plan_id,
                models.RrwebSession.payload["order_plan_id"].as_string() == order_plan_id_str,
            )
        )
    return query


def get_events(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    company_id: Optional[int] = None,
    user_id: Optional[int] = None,
    company_name: Optional[str] = None,
    order_plan_id: Optional[int] = None,
) -> Tuple[int, List[models.RrwebSession]]:
    """
    查询录屏会话列表，按 updated_at 降序。
    支持公司/用户/订单精确筛选与公司名模糊筛选。
    """
    query = _apply_list_filters(
        db.query(models.RrwebSession),
        company_id=company_id,
        user_id=user_id,
        company_name=company_name,
        order_plan_id=order_plan_id,
    )
    count = query.count()
    results = (
        query.order_by(models.RrwebSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return count, results


def create_event(db: Session, event: schemas.EventCreate) -> models.RrwebSession:
    """
    按三元组 upsert 会话，并插入一条事件分片。
    返回更新后的会话（供列表字段展示）。
    """
    ins_session = (
        db.query(models.RrwebSession)
        .filter(
            models.RrwebSession.request_id == event.request_id,
            models.RrwebSession.company_id == event.company_id,
            models.RrwebSession.user_id == event.user_id,
        )
        .first()
    )
    now = get_now()
    if ins_session:
        ins_session.company_name = event.company_name
        ins_session.user_name = event.user_name
        ins_session.record_type = event.record_type
        ins_session.payload = event.payload or {}
        ins_session.updated_at = now
    else:
        ins_session = models.RrwebSession(
            request_id=event.request_id,
            company_id=event.company_id,
            company_name=event.company_name,
            user_id=event.user_id,
            user_name=event.user_name,
            record_type=event.record_type,
            payload=event.payload or {},
            created_at=now,
            updated_at=now,
        )
        db.add(ins_session)
        db.flush()

    ins_detail = models.RrwebEventDetail(
        session_id=ins_session.id,
        events=event.events,
        created_at=now,
        updated_at=now,
    )
    db.add(ins_detail)
    db.commit()
    db.refresh(ins_session)
    return ins_session
