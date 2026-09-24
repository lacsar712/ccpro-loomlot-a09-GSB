from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.shift_handover import ShiftHandover
from app.models.user import User
from app.schemas.shift_handover import (
    ShiftHandoverConfirm,
    ShiftHandoverCreate,
    ShiftHandoverUpdate,
    ShiftHandoverOut,
)

router = APIRouter(prefix="/api/shift-handovers", tags=["shift-handovers"])

ADMIN_ROLE = "admin"


def pending_handover_count(db: Session) -> int:
    """待接交接条数：接班确认时刻为空的交接班。"""
    return (
        db.query(func.count(ShiftHandover.id))
        .filter(ShiftHandover.confirmed_at.is_(None))
        .scalar()
        or 0
    )


def ensure_no_pending_handover(db: Session) -> None:
    """存在待接交接时全场禁开：新建染程与新建色牢度抽检统一走此拦截。"""
    n = pending_handover_count(db)
    if n > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"存在 {n} 条待接夜班交接，全场暂停新建染程与色牢度抽检，接班确认后恢复",
        )


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


@router.get("", response_model=List[ShiftHandoverOut])
def list_handovers(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(ShiftHandover).order_by(ShiftHandover.id.desc()).all()


@router.post("", response_model=ShiftHandoverOut, status_code=status.HTTP_201_CREATED)
def create_handover(
    payload: ShiftHandoverCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if payload.handover_by == payload.successor:
        raise HTTPException(status_code=400, detail="交班人与接班人不得相同")
    item = ShiftHandover(
        handover_by=payload.handover_by,
        successor=payload.successor,
        handed_at=payload.handed_at,
        confirmed_at=None,
        dyeing_vat_count=payload.dyeing_vat_count,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{handover_id}", response_model=ShiftHandoverOut)
def get_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(ShiftHandover).filter(ShiftHandover.id == handover_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交接班不存在")
    return item


@router.put("/{handover_id}", response_model=ShiftHandoverOut)
def update_handover(
    handover_id: int,
    payload: ShiftHandoverUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(ShiftHandover).filter(ShiftHandover.id == handover_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交接班不存在")
    data = payload.model_dump(exclude_unset=True)
    handover_by = data.get("handover_by", item.handover_by)
    successor = data.get("successor", item.successor)
    if handover_by == successor:
        raise HTTPException(status_code=400, detail="交班人与接班人不得相同")
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{handover_id}/confirm", response_model=ShiftHandoverOut)
def confirm_handover(
    handover_id: int,
    payload: ShiftHandoverConfirm = ShiftHandoverConfirm(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(ShiftHandover).filter(ShiftHandover.id == handover_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交接班不存在")
    is_successor = item.successor in {current_user.display_name, current_user.username}
    if current_user.role != ADMIN_ROLE and not is_successor:
        raise HTTPException(status_code=403, detail="仅接班人本人或主管可确认接班")
    if item.confirmed_at is not None:
        raise HTTPException(status_code=409, detail="该交接班已确认接班")
    confirmed_at = payload.confirmed_at or datetime.now(timezone.utc)
    if _as_aware(confirmed_at) < _as_aware(item.handed_at):
        raise HTTPException(status_code=400, detail="确认时刻不得早于交班时刻")
    item.confirmed_at = confirmed_at
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{handover_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_handover(
    handover_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(ShiftHandover).filter(ShiftHandover.id == handover_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交接班不存在")
    db.delete(item)
    db.commit()
