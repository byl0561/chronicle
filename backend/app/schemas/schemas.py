from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Tab ──────────────────────────────────────────────────────────────────────

class TabCreate(BaseModel):
    name: str
    color: Optional[str] = None
    sort: int = 0


class TabUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort: Optional[int] = None


class TabOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: Optional[str]
    sort: int


# ── Indicator ─────────────────────────────────────────────────────────────────

class IndicatorCreate(BaseModel):
    name: str
    unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    direction: str = "range"
    sort: int = 0


class IndicatorUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    direction: Optional[str] = None
    sort: Optional[int] = None


class TrendPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    value: float
    measured_at: date
    # 该记录的有效参考区间（记录自带优先，否则回退指标默认），供前端归一化
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None


class LatestValue(BaseModel):
    value: float
    measured_at: date
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None


class IndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tab_id: int
    name: str
    unit: Optional[str]
    ref_low: Optional[float]
    ref_high: Optional[float]
    direction: str
    sort: int
    latest_value: Optional[LatestValue] = None
    trend_values: list[TrendPoint] = []


# ── Record ────────────────────────────────────────────────────────────────────

class RecordCreate(BaseModel):
    value: float
    measured_at: date
    note: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    source: Optional[str] = None


class RecordUpdate(BaseModel):
    value: Optional[float] = None
    measured_at: Optional[date] = None
    note: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    source: Optional[str] = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    indicator_id: int
    value: float
    measured_at: date
    note: Optional[str]
    ref_low: Optional[float]
    ref_high: Optional[float]
    source: Optional[str]
    created_at: datetime


# ── Reorder ───────────────────────────────────────────────────────────────────

class ReorderItem(BaseModel):
    id: int
    sort: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]
