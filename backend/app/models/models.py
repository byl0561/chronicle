from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tab(Base):
    __tablename__ = "tabs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    indicators: Mapped[list[Indicator]] = relationship(
        back_populates="tab",
        cascade="all, delete-orphan",
        order_by="Indicator.sort",
    )


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tab_id: Mapped[int] = mapped_column(
        ForeignKey("tabs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ref_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ref_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # lower: 越低越好（超过 ref_high 为越界）
    # higher: 越高越好（低于 ref_low 为越界）
    # range: 在 [ref_low, ref_high] 内为正常
    direction: Mapped[str] = mapped_column(String(10), default="range", nullable=False)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    tab: Mapped[Tab] = relationship(back_populates="indicators")
    records: Mapped[list[Record]] = relationship(
        back_populates="indicator",
        cascade="all, delete-orphan",
        order_by="Record.measured_at",
    )


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    measured_at: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 本次化验单印的参考区间；为空时回退到 Indicator 的默认区间
    ref_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ref_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # 检测来源（医院/方法），自由文本，前端按历史值下拉补全
    source: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    indicator: Mapped[Indicator] = relationship(back_populates="records")
