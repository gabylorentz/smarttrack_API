"""Endpoints relacionados a Leituras (Readings)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.reading import Reading
from app.schemas.reading import ReadingCreate, ReadingResponse
from app.services.vegetation import calcular_vegetation_status

router = APIRouter(tags=["Readings"])


def _to_reading_response(reading: Reading, device_business_id: str) -> ReadingResponse:
    return ReadingResponse(
        id=reading.id,
        device_id=device_business_id,
        timestamp=reading.timestamp,
        laser_status=reading.laser_status,
        vegetation_status=reading.vegetation_status,
        height_limit_cm=reading.height_limit_cm,
        duracao_interrupcao_seg=reading.duracao_interrupcao_seg or 0.0,
        created_at=reading.created_at,
    )


@router.post("/readings", response_model=ReadingResponse, status_code=status.HTTP_201_CREATED)
def create_reading(reading: ReadingCreate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == reading.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispositivo '{reading.device_id}' não encontrado. Cadastre o dispositivo antes de enviar leituras.",
        )

    vegetation_status = calcular_vegetation_status(reading.laser_status)

    nova_leitura = Reading(
        device_id=device.id,
        timestamp=reading.timestamp,
        laser_status=reading.laser_status.value,
        vegetation_status=vegetation_status.value,
        height_limit_cm=reading.height_limit_cm,
        duracao_interrupcao_seg=reading.duracao_interrupcao_seg,
    )
    db.add(nova_leitura)
    db.commit()
    db.refresh(nova_leitura)

    return _to_reading_response(nova_leitura, device.device_id)


@router.get("/readings", response_model=List[ReadingResponse])
def list_readings(
    vegetation_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Reading)
    if vegetation_status:
        query = query.filter(Reading.vegetation_status == vegetation_status)

    leituras = query.order_by(Reading.timestamp.desc()).limit(limit).all()

    resultado = []
    for leitura in leituras:
        device = db.query(Device).filter(Device.id == leitura.device_id).first()
        resultado.append(_to_reading_response(leitura, device.device_id if device else "DESCONHECIDO"))
    return resultado


@router.get("/readings/{device_id}", response_model=List[ReadingResponse])
def get_readings_by_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispositivo '{device_id}' não encontrado")

    leituras = (
        db.query(Reading)
        .filter(Reading.device_id == device.id)
        .order_by(Reading.timestamp.desc())
        .all()
    )
    return [_to_reading_response(r, device_id) for r in leituras]
