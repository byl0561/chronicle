from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.models import Indicator, Tab
from app.schemas.schemas import (
    IndicatorCreate,
    IndicatorOut,
    IndicatorUpdate,
    LatestValue,
    ReorderRequest,
    TrendPoint,
)

router = APIRouter(tags=["indicators"])

TREND_LIMIT = 30  # 趋势图最多取最近 N 条记录


def _enrich(indicator: Indicator) -> IndicatorOut:
    records = sorted(indicator.records, key=lambda r: r.measured_at)

    def eff_low(r):
        return r.ref_low if r.ref_low is not None else indicator.ref_low

    def eff_high(r):
        return r.ref_high if r.ref_high is not None else indicator.ref_high

    latest = None
    if records:
        last = records[-1]
        latest = LatestValue(
            value=last.value,
            measured_at=last.measured_at,
            ref_low=eff_low(last),
            ref_high=eff_high(last),
        )
    trend = [
        TrendPoint(
            value=r.value,
            measured_at=r.measured_at,
            ref_low=eff_low(r),
            ref_high=eff_high(r),
        )
        for r in records[-TREND_LIMIT:]
    ]
    out = IndicatorOut.model_validate(indicator)
    out.latest_value = latest
    out.trend_values = trend
    return out


@router.get("/tabs/{tab_id}/indicators", response_model=list[IndicatorOut])
def list_indicators(tab_id: int, db: Session = Depends(get_db)):
    if not db.get(Tab, tab_id):
        raise HTTPException(404, "分类不存在")
    indicators = (
        db.query(Indicator)
        .filter(Indicator.tab_id == tab_id)
        .order_by(Indicator.sort, Indicator.id)
        .all()
    )
    return [_enrich(i) for i in indicators]


@router.post("/tabs/{tab_id}/indicators", response_model=IndicatorOut, status_code=201)
def create_indicator(tab_id: int, data: IndicatorCreate, db: Session = Depends(get_db)):
    if not db.get(Tab, tab_id):
        raise HTTPException(404, "分类不存在")
    ind = Indicator(tab_id=tab_id, **data.model_dump())
    db.add(ind)
    db.commit()
    db.refresh(ind)
    return _enrich(ind)


@router.patch("/indicators/{indicator_id}", response_model=IndicatorOut)
def update_indicator(indicator_id: int, data: IndicatorUpdate, db: Session = Depends(get_db)):
    ind = db.get(Indicator, indicator_id)
    if not ind:
        raise HTTPException(404, "指标不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(ind, k, v)
    db.commit()
    db.refresh(ind)
    return _enrich(ind)


@router.delete("/indicators/{indicator_id}", status_code=204)
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    ind = db.get(Indicator, indicator_id)
    if not ind:
        raise HTTPException(404, "指标不存在")
    db.delete(ind)
    db.commit()


@router.post("/indicators/reorder", status_code=204)
def reorder_indicators(data: ReorderRequest, db: Session = Depends(get_db)):
    for item in data.items:
        ind = db.get(Indicator, item.id)
        if ind:
            ind.sort = item.sort
    db.commit()
