"""Endpoints relacionados a Dispositivos (Devices)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.reading import Reading
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceStatusResponse

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um dispositivo cadastrado com device_id '{device.device_id}'",
        )

    novo_device = Device(
        device_id=device.device_id,
        name=device.name,
        location=device.location,
        latitude=device.latitude,
        longitude=device.longitude,
        status=device.status.value if device.status else "ACTIVE",
    )
    db.add(novo_device)
    db.commit()
    db.refresh(novo_device)
    return novo_device


@router.get("", response_model=List[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).order_by(Device.created_at.desc()).all()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispositivo '{device_id}' não encontrado")
    return device


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
def get_device_status(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispositivo '{device_id}' não encontrado")

    ultima_leitura = (
        db.query(Reading)
        .filter(Reading.device_id == device.id)
        .order_by(Reading.timestamp.desc())
        .first()
    )

    if not ultima_leitura:
        return DeviceStatusResponse(
            device_id=device_id, vegetation_status=None, laser_status=None,
            last_reading_at=None, message="Nenhuma leitura registrada ainda para este dispositivo.",
        )

    return DeviceStatusResponse(
        device_id=device_id,
        vegetation_status=ultima_leitura.vegetation_status,
        laser_status=ultima_leitura.laser_status,
        last_reading_at=ultima_leitura.timestamp,
        message="Situação obtida a partir da leitura mais recente.",
    )
