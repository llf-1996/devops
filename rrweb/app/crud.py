from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional, Tuple
from sqlalchemy import func, and_

def get_event(db: Session, request_id: str, company_id: int, user_id: int) -> List[models.Event]:
    return db.query(models.Event).filter(
        models.Event.request_id == request_id,
        models.Event.company_id == company_id,
        models.Event.user_id == user_id
    ).order_by(models.Event.created_at.asc()).all()

def get_events(db: Session, skip: int = 0, limit: int = 20) -> Tuple[int, List[models.Event]]:
    subq = db.query(
        models.Event.request_id,
        models.Event.company_id,
        models.Event.user_id,
        func.max(models.Event.created_at).label('max_created_at')
    ).group_by(
        models.Event.request_id,
        models.Event.company_id,
        models.Event.user_id
    ).subquery()

    query = db.query(models.Event).join(
        subq,
        and_(
            models.Event.request_id == subq.c.request_id,
            models.Event.company_id == subq.c.company_id,
            models.Event.user_id == subq.c.user_id,
            models.Event.created_at == subq.c.max_created_at
        )
    )
    count = query.count()
    results = query.order_by(models.Event.created_at.desc()).offset(skip).limit(limit).all()
    return count, results


def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    db_event = models.Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
