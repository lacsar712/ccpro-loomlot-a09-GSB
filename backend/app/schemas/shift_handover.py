from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ShiftHandoverCreate(BaseModel):
    handover_by: str = Field(..., min_length=1, max_length=64, alias="handoverBy")
    successor: str = Field(..., min_length=1, max_length=64, alias="successor")
    handed_at: datetime = Field(..., alias="handedAt")
    dyeing_vat_count: int = Field(..., ge=0, alias="dyeingVatCount")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ShiftHandoverUpdate(BaseModel):
    # confirmed_at 不在此开放，接班确认只能走 /confirm 接口
    handover_by: Optional[str] = Field(None, min_length=1, max_length=64, alias="handoverBy")
    successor: Optional[str] = Field(None, min_length=1, max_length=64, alias="successor")
    handed_at: Optional[datetime] = Field(None, alias="handedAt")
    dyeing_vat_count: Optional[int] = Field(None, ge=0, alias="dyeingVatCount")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ShiftHandoverConfirm(BaseModel):
    confirmed_at: Optional[datetime] = Field(None, alias="confirmedAt")

    model_config = ConfigDict(populate_by_name=True)


class ShiftHandoverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    handover_by: str = Field(serialization_alias="handoverBy")
    successor: str = Field(serialization_alias="successor")
    handed_at: datetime = Field(serialization_alias="handedAt")
    confirmed_at: Optional[datetime] = Field(default=None, serialization_alias="confirmedAt")
    dyeing_vat_count: int = Field(serialization_alias="dyeingVatCount")
    notes: Optional[str] = None
