from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models, schemas
from .utils.datetime_utils import get_now


class SessionLockedError(Exception):
    """会话已锁定，禁止删除。"""


class SessionNotFoundError(Exception):
    """会话不存在。"""


def get_event_details(
    db: Session, request_id: str, company_id: int, user_id: int
) -> List[models.RrwebEventDetail]:
    """按会话定位后返回事件分片：有 seq 按 seq，空 seq 再按 id。"""
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
        .order_by(
            models.RrwebEventDetail.seq.asc(),
            models.RrwebEventDetail.id.asc(),
        )
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


def get_session_by_id(db: Session, session_id: int) -> Optional[models.RrwebSession]:
    """按主键查询录屏会话。"""
    return db.query(models.RrwebSession).filter(models.RrwebSession.id == session_id).first()


def set_session_locked(db: Session, session_id: int, locked: bool) -> models.RrwebSession:
    """设置会话锁定状态；会话不存在则抛 SessionNotFoundError。"""
    ins_session = get_session_by_id(db, session_id)
    if not ins_session:
        raise SessionNotFoundError(f"会话不存在: id={session_id}")
    ins_session.is_locked = 1 if locked else 0
    ins_session.updated_at = get_now()
    db.commit()
    db.refresh(ins_session)
    return ins_session


def _delete_session_and_details(db: Session, ins_session: models.RrwebSession) -> None:
    """删除会话及其事件分片（调用方保证未锁定）。"""
    db.query(models.RrwebEventDetail).filter(
        models.RrwebEventDetail.session_id == ins_session.id
    ).delete(synchronize_session=False)
    db.delete(ins_session)


def delete_session(db: Session, session_id: int) -> int:
    """
    删除单个录屏会话及其分片。
    已锁定抛 SessionLockedError；不存在抛 SessionNotFoundError。
    返回已删除的会话 id。
    """
    ins_session = get_session_by_id(db, session_id)
    if not ins_session:
        raise SessionNotFoundError(f"会话不存在: id={session_id}")
    if ins_session.is_locked:
        raise SessionLockedError("已锁定，无法删除")
    deleted_id = ins_session.id
    _delete_session_and_details(db, ins_session)
    db.commit()
    return deleted_id


def cleanup_unlocked_sessions(db: Session, older_than: datetime) -> int:
    """
    清理未锁定且 updated_at 早于 older_than 的会话及其分片。
    返回删除的会话条数。
    """
    qs_session = (
        db.query(models.RrwebSession)
        .filter(
            models.RrwebSession.is_locked == 0,
            models.RrwebSession.updated_at < older_than,
        )
        .all()
    )
    deleted_count = 0
    for ins_session in qs_session:
        _delete_session_and_details(db, ins_session)
        deleted_count += 1
    db.commit()
    return deleted_count


def create_event(db: Session, event: schemas.EventCreate) -> models.RrwebSession:
    """
    按三元组 upsert 会话，并插入一条事件分片。
    更新已有会话时不覆盖 is_locked。
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
            is_locked=0,
            payload=event.payload or {},
            created_at=now,
            updated_at=now,
        )
        db.add(ins_session)
        db.flush()

    ins_detail = models.RrwebEventDetail(
        session_id=ins_session.id,
        seq=event.seq,
        events=event.events,
        created_at=now,
        updated_at=now,
    )
    db.add(ins_detail)
    db.commit()
    db.refresh(ins_session)
    return ins_session
