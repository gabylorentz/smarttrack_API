"""Regra de negócio determinística: laser_status -> vegetation_status."""

from app.core.enums import LaserStatus, VegetationStatus


def calcular_vegetation_status(laser_status: LaserStatus) -> VegetationStatus:
    if laser_status == LaserStatus.DETECTED:
        return VegetationStatus.WITHIN_LIMIT
    elif laser_status == LaserStatus.INTERRUPTED:
        return VegetationStatus.ABOVE_LIMIT
    else:
        raise ValueError(f"laser_status desconhecido: {laser_status}")
