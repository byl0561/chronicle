import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.models import Indicator, Record, Tab

router = APIRouter(prefix="/data", tags=["data"])

HEADERS = [
    "tab_name", "tab_color",
    "indicator_name", "unit", "ref_low", "ref_high", "direction",
    "measured_at", "value", "note",
    # 记录级参考区间（本次化验单，空则继承指标默认）与检测来源
    "record_ref_low", "record_ref_high", "source",
]


@router.get("/export")
def export_csv(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()

    tabs = db.query(Tab).order_by(Tab.sort, Tab.id).all()
    for tab in tabs:
        for ind in sorted(tab.indicators, key=lambda x: (x.sort, x.id)):
            records = sorted(ind.records, key=lambda r: r.measured_at)
            if records:
                for rec in records:
                    writer.writerow({
                        "tab_name": tab.name,
                        "tab_color": tab.color or "",
                        "indicator_name": ind.name,
                        "unit": ind.unit or "",
                        "ref_low": "" if ind.ref_low is None else ind.ref_low,
                        "ref_high": "" if ind.ref_high is None else ind.ref_high,
                        "direction": ind.direction,
                        "measured_at": rec.measured_at.isoformat(),
                        "value": rec.value,
                        "note": rec.note or "",
                        "record_ref_low": "" if rec.ref_low is None else rec.ref_low,
                        "record_ref_high": "" if rec.ref_high is None else rec.ref_high,
                        "source": rec.source or "",
                    })
            else:
                # 导出无记录的指标行，方便保留指标配置
                writer.writerow({
                    "tab_name": tab.name,
                    "tab_color": tab.color or "",
                    "indicator_name": ind.name,
                    "unit": ind.unit or "",
                    "ref_low": "" if ind.ref_low is None else ind.ref_low,
                    "ref_high": "" if ind.ref_high is None else ind.ref_high,
                    "direction": ind.direction,
                    "measured_at": "",
                    "value": "",
                    "note": "",
                })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=chronicle_export.csv"},
    )


@router.post("/import")
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    tab_cache: dict[str, Tab] = {}
    ind_cache: dict[tuple, Indicator] = {}
    imported = {"tabs": 0, "indicators": 0, "records": 0, "skipped": 0}

    for row in reader:
        tab_name = (row.get("tab_name") or "").strip()
        ind_name = (row.get("indicator_name") or "").strip()
        if not tab_name or not ind_name:
            continue

        if tab_name not in tab_cache:
            tab = db.query(Tab).filter(Tab.name == tab_name).first()
            if not tab:
                max_sort = db.query(Tab).count()
                tab = Tab(name=tab_name, color=row.get("tab_color") or None, sort=max_sort)
                db.add(tab)
                db.flush()
                imported["tabs"] += 1
            tab_cache[tab_name] = tab
        tab = tab_cache[tab_name]

        key = (tab.id, ind_name)
        if key not in ind_cache:
            ind = db.query(Indicator).filter(
                Indicator.tab_id == tab.id, Indicator.name == ind_name
            ).first()
            if not ind:
                max_sort = db.query(Indicator).filter(Indicator.tab_id == tab.id).count()
                try:
                    ref_low = float(row["ref_low"]) if row.get("ref_low", "").strip() else None
                    ref_high = float(row["ref_high"]) if row.get("ref_high", "").strip() else None
                except ValueError:
                    ref_low = ref_high = None
                ind = Indicator(
                    tab_id=tab.id,
                    name=ind_name,
                    unit=row.get("unit") or None,
                    ref_low=ref_low,
                    ref_high=ref_high,
                    direction=row.get("direction") or "range",
                    sort=max_sort,
                )
                db.add(ind)
                db.flush()
                imported["indicators"] += 1
            ind_cache[key] = ind
        ind = ind_cache[key]

        val_str = (row.get("value") or "").strip()
        date_str = (row.get("measured_at") or "").strip()
        if val_str and date_str:
            try:
                val = float(val_str)
                measured_at = date.fromisoformat(date_str)
            except ValueError:
                imported["skipped"] += 1
                continue
            exists = db.query(Record).filter(
                Record.indicator_id == ind.id,
                Record.measured_at == measured_at,
            ).first()
            if exists:
                imported["skipped"] += 1
            else:
                try:
                    rec_low = float(row["record_ref_low"]) if row.get("record_ref_low", "").strip() else None
                    rec_high = float(row["record_ref_high"]) if row.get("record_ref_high", "").strip() else None
                except ValueError:
                    rec_low = rec_high = None
                db.add(Record(
                    indicator_id=ind.id,
                    value=val,
                    measured_at=measured_at,
                    note=row.get("note") or None,
                    ref_low=rec_low,
                    ref_high=rec_high,
                    source=(row.get("source") or "").strip() or None,
                ))
                imported["records"] += 1

    db.commit()
    return {"imported": imported}
