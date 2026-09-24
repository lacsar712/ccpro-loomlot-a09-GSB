from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.handover_guard import pending_handover_count
from app.models.night_handover import NightHandover
from app.models.user import User
from app.models.vat import Vat
from app.schemas.night_handover import NightHandoverCreate, NightHandoverOut

router = APIRouter(prefix="/api/night-handovers", tags=["night-handovers"])


class ConfirmBody(BaseModel):
    confirmed_at: Optional[datetime] = Field(None, alias="confirmedAt")

    model_config = ConfigDict(populate_by_name=True)


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _get_user(db: Session, user_id: int, what: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail=f"{what}不存在")
    return user


@router.get("", response_model=List[NightHandoverOut])
def list_handovers(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(NightHandover)
    if status_filter == "pending":
        q = q.filter(NightHandover.confirmed_at.is_(None))
    elif status_filter == "confirmed":
        q = q.filter(NightHandover.confirmed_at.is_not(None))
    return q.order_by(NightHandover.id.desc()).all()


@router.get("/pending-count")
def get_pending_count(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return {"pendingCount": pending_handover_count(db)}


@router.post("", response_model=NightHandoverOut, status_code=status.HTTP_201_CREATED)
def create_handover(
    payload: NightHandoverCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if payload.handover_by_id == payload.takeover_by_id:
        raise HTTPException(status_code=400, detail="交班人与接班人不得相同")
    _get_user(db, payload.handover_by_id, "交班人")
    _get_user(db, payload.takeover_by_id, "接班人")

    # 在染缸数快照：交班时刻处于 dyeing 的染缸数
    active_vat_count = (
        db.query(Vat).filter(Vat.status == "dyeing").count()
    )

    item = NightHandover(
        handover_by_id=payload.handover_by_id,
        takeover_by_id=payload.takeover_by_id,
        handed_at=payload.handed_at,
        confirmed_at=None,
        active_vat_count=active_vat_count,
        notes=(payload.notes.strip() if payload.notes and payload.notes.strip() else None),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{handover_id}/confirm", response_model=NightHandoverOut)
def confirm_handover(
    handover_id: int,
    body: Optional[ConfirmBody] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(NightHandover).filter(NightHandover.id == handover_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="夜班交接条不存在")

    # 仅接班人本人或主管可确认
    if current_user.id != item.takeover_by_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅接班人本人或主管可确认接班")

    if item.confirmed_at is not None:
        raise HTTPException(status_code=409, detail="该交接条已完成接班确认，无需重复确认")

    confirmed_at = body.confirmed_at if body and body.confirmed_at else datetime.now(timezone.utc)
    confirmed_at = _as_aware(confirmed_at)
    handed = _as_aware(item.handed_at)
    if confirmed_at < handed:
        raise HTTPException(status_code=400, detail="接班确认时刻不得早于交班时刻")

    item.confirmed_at = confirmed_at
    db.commit()
    db.refresh(item)
    return item
