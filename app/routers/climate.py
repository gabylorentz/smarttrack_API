"""
Endpoints relacionados a dados climáticos (ClimateReading).

Criado para alimentar o modelo de Machine Learning (ver
routers/predictions.py), que precisa de temperatura, umidade, chuva e
radiação solar diárias para cada dispositivo.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.climate_reading import ClimateReading
from app.schemas.climate import ClimateReadingCreate, ClimateReadingResponse

router = APIRouter(prefix="/climate-readings", tags=["Climate"])


def _to_response(cr: ClimateReading, device_business_id: str) -> ClimateReadingResponse:
    return ClimateReadingResponse(
        id=cr.id, device_id=device_business_id, date=cr.date, temp_c=cr.temp_c,
        umidade_pct=cr.umidade_pct, chuva_mm_mes=cr.chuva_mm_mes,
        radiacao_mj_m2_dia=cr.radiacao_mj_m2_dia, umidade_solo_proxy=cr.umidade_solo_proxy,
    )


@router.post("", response_model=ClimateReadingResponse, status_code=status.HTTP_201_CREATED)
def create_climate_reading(payload: ClimateReadingCreate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispositivo '{payload.device_id}' não encontrado. Cadastre o dispositivo antes de enviar dados climáticos.",
        )

    existente = (
        db.query(ClimateReading)
        .filter(ClimateReading.device_id == device.id, ClimateReading.date == payload.date)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um registro climático para '{payload.device_id}' na data {payload.date}.",
        )

    novo = ClimateReading(
        device_id=device.id, date=payload.date, temp_c=payload.temp_c,
        umidade_pct=payload.umidade_pct, chuva_mm_mes=payload.chuva_mm_mes,
        radiacao_mj_m2_dia=payload.radiacao_mj_m2_dia, umidade_solo_proxy=payload.umidade_solo_proxy,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return _to_response(novo, device.device_id)


@router.get("/{device_id}", response_model=List[ClimateReadingResponse])
def list_climate_readings(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispositivo '{device_id}' não encontrado")

    registros = (
        db.query(ClimateReading)
        .filter(ClimateReading.device_id == device.id)
        .order_by(ClimateReading.date.desc())
        .all()
    )
    return [_to_response(r, device_id) for r in registros]
