from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud
from app.database import SessionLocal

app = FastAPI()

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


@app.get("/events", response_model=dict)
def list_events(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    skip = (page - 1) * page_size
    count, results = crud.get_events(db, skip=skip, limit=page_size)
    results_out = [schemas.EventListOut.model_validate(r) for r in results]
    return {"count": count, "results": results_out}


@app.get("/events/detail", response_model=List[schemas.EventDetailOut])
def get_event(
    request_id: str,
    company_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    return crud.get_event(db, request_id, company_id, user_id)


@app.post("/events", response_model=schemas.EventListOut)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, event)
