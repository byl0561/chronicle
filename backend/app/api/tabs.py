from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.models import Tab
from app.schemas.schemas import ReorderRequest, TabCreate, TabOut, TabUpdate

router = APIRouter(prefix="/tabs", tags=["tabs"])


@router.get("", response_model=list[TabOut])
def list_tabs(db: Session = Depends(get_db)):
    return db.query(Tab).order_by(Tab.sort, Tab.id).all()


@router.post("", response_model=TabOut, status_code=201)
def create_tab(data: TabCreate, db: Session = Depends(get_db)):
    tab = Tab(**data.model_dump())
    db.add(tab)
    db.commit()
    db.refresh(tab)
    return tab


@router.patch("/{tab_id}", response_model=TabOut)
def update_tab(tab_id: int, data: TabUpdate, db: Session = Depends(get_db)):
    tab = db.get(Tab, tab_id)
    if not tab:
        raise HTTPException(404, "分类不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(tab, k, v)
    db.commit()
    db.refresh(tab)
    return tab


@router.delete("/{tab_id}", status_code=204)
def delete_tab(tab_id: int, db: Session = Depends(get_db)):
    tab = db.get(Tab, tab_id)
    if not tab:
        raise HTTPException(404, "分类不存在")
    db.delete(tab)
    db.commit()


@router.post("/reorder", status_code=204)
def reorder_tabs(data: ReorderRequest, db: Session = Depends(get_db)):
    for item in data.items:
        tab = db.get(Tab, item.id)
        if tab:
            tab.sort = item.sort
    db.commit()
