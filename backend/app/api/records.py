from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.models import Indicator, Record
from app.schemas.schemas import RecordCreate, RecordOut, RecordUpdate

router = APIRouter(tags=["records"])


@router.get("/sources", response_model=list[str])
def list_sources(db: Session = Depends(get_db)):
    """所有历史检测来源（医院/方法），按使用次数降序，供录入时下拉补全。"""
    rows = (
        db.query(Record.source, func.count(Record.id).label("n"))
        .filter(Record.source.isnot(None), Record.source != "")
        .group_by(Record.source)
        .order_by(func.count(Record.id).desc())
        .all()
    )
    return [r[0] for r in rows]


@router.get("/indicators/{indicator_id}/records", response_model=list[RecordOut])
def list_records(indicator_id: int, db: Session = Depends(get_db)):
    if not db.get(Indicator, indicator_id):
        raise HTTPException(404, "指标不存在")
    return (
        db.query(Record)
        .filter(Record.indicator_id == indicator_id)
        .order_by(Record.measured_at.desc())
        .all()
    )


@router.post("/indicators/{indicator_id}/records", response_model=RecordOut, status_code=201)
def create_record(indicator_id: int, data: RecordCreate, db: Session = Depends(get_db)):
    if not db.get(Indicator, indicator_id):
        raise HTTPException(404, "指标不存在")
    rec = Record(indicator_id=indicator_id, **data.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.patch("/records/{record_id}", response_model=RecordOut)
def update_record(record_id: int, data: RecordUpdate, db: Session = Depends(get_db)):
    rec = db.get(Record, record_id)
    if not rec:
        raise HTTPException(404, "记录不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(rec, k, v)
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/records/{record_id}", status_code=204)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.get(Record, record_id)
    if not rec:
        raise HTTPException(404, "记录不存在")
    db.delete(rec)
    db.commit()
