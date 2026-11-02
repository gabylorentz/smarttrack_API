"""Schemas Pydantic para o recurso Device."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.enums import DeviceStatus


class DeviceCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=50, examples=["ST001"])
    name: str = Field(..., min_length=1, max_length=100, examples=["Sensor KM 45"])
    location: str = Field(..., min_length=1, max_length=200, examples=["Rodovia BR-101, KM 45"])
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    status: Optional[DeviceStatus] = DeviceStatus.ACTIVE

    @field_validator("device_id")
    @classmethod
    def device_id_nao_pode_ser_vazio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("device_id não pode ser vazio ou conter apenas espaços")
        return v


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceStatusResponse(BaseModel):
    device_id: str
    vegetation_status: Optional[str] = None
    laser_status: Optional[str] = None
    last_reading_at: Optional[datetime] = None
    message: str
