from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class NightHandover(Base):
    """夜班交接班条：未写接班确认时刻即为待接。"""

    __tablename__ = "night_handovers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    handover_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    takeover_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    handed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    active_vat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    handover_by: Mapped["User"] = relationship("User", foreign_keys=[handover_by_id])
    takeover_by: Mapped["User"] = relationship("User", foreign_keys=[takeover_by_id])

    @property
    def handover_by_name(self) -> Optional[str]:
        return self.handover_by.display_name if self.handover_by else None

    @property
    def takeover_by_name(self) -> Optional[str]:
        return self.takeover_by.display_name if self.takeover_by else None

    @property
    def is_pending(self) -> bool:
        return self.confirmed_at is None
