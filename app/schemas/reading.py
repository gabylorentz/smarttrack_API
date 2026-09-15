"""Schemas Pydantic para o recurso Reading (leitura)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import LaserStatus


class ReadingCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=50, examples=["ST001"])
    timestamp: datetime = Field(..., examples=["2026-09-12T20:30:00"])
    laser_status: LaserStatus
    height_limit_cm: int = Field(..., gt=0, le=1000, examples=[15])
    duracao_interrupcao_seg: float = Field(
        default=0.0, ge=0, le=86400,
        description="Duração da interrupção do feixe, em segundos (0 se não interrompido).",
    )

    @field_validator("timestamp")
    @classmethod
    def timestamp_nao_pode_ser_futuro_distante(cls, v: datetime) -> datetime:
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v > now.replace(year=now.year + 1):
            raise ValueError("timestamp está muito distante no futuro")
        return v


class ReadingResponse(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    laser_status: str
    vegetation_status: str
    height_limit_cm: int
    duracao_interrupcao_seg: float
    created_at: datetime

    model_config = {"from_attributes": True}
