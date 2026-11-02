"""Schemas Pydantic para o recurso ClimateReading (dados climáticos)."""

from datetime import date as date_type

from pydantic import BaseModel, Field


class ClimateReadingCreate(BaseModel):
    device_id: str = Field(..., examples=["ST001"])
    date: date_type = Field(..., examples=["2026-09-12"])
    temp_c: float = Field(..., ge=-10, le=50)
    umidade_pct: float = Field(..., ge=0, le=100)
    chuva_mm_mes: float = Field(..., ge=0, le=1000)
    radiacao_mj_m2_dia: float = Field(..., ge=0, le=40)
    umidade_solo_proxy: float = Field(default=0.25, ge=0, le=1)


class ClimateReadingResponse(ClimateReadingCreate):
    id: int

    model_config = {"from_attributes": True}
