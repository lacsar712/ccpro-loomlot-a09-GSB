"""夜班交接待接拦截：存在待接交接时，全场禁止开立新染程 / 新色牢度抽检。

拦截点必须落在后端开立接口上，交接条与开立拦截不得脱节。
"""

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.night_handover import NightHandover


def pending_handover_count(db: Session) -> int:
    return (
        db.query(func.count(NightHandover.id))
        .filter(NightHandover.confirmed_at.is_(None))
        .scalar()
        or 0
    )


def ensure_no_pending_handover(db: Session, action: str) -> None:
    """action 例：「新建染程」「新建色牢度抽检」。"""
    pending = pending_handover_count(db)
    if pending:
        raise HTTPException(
            status_code=409,
            detail=(
                f"存在 {pending} 条夜班交接待接班确认，接班确认前全场禁止{action}"
            ),
        )
