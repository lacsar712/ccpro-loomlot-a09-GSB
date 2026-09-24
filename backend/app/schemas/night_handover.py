from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NightHandoverCreate(BaseModel):
    handover_by_id: int = Field(..., alias="handoverById")
    takeover_by_id: int = Field(..., alias="takeoverById")
    handed_at: datetime = Field(..., alias="handedAt")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class NightHandoverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    handover_by_id: int = Field(serialization_alias="handoverById")
    handover_by_name: Optional[str] = Field(serialization_alias="handoverByName")
    takeover_by_id: int = Field(serialization_alias="takeoverById")
    takeover_by_name: Optional[str] = Field(serialization_alias="takeoverByName")
    handed_at: datetime = Field(serialization_alias="handedAt")
    confirmed_at: Optional[datetime] = Field(serialization_alias="confirmedAt")
    active_vat_count: int = Field(serialization_alias="activeVatCount")
    notes: Optional[str] = None
    is_pending: bool = Field(serialization_alias="isPending")
