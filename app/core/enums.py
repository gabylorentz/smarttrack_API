"""Enums usados em toda a aplicação."""

from enum import Enum


class LaserStatus(str, Enum):
    DETECTED = "DETECTED"
    INTERRUPTED = "INTERRUPTED"


class VegetationStatus(str, Enum):
    WITHIN_LIMIT = "WITHIN_LIMIT"
    ABOVE_LIMIT = "ABOVE_LIMIT"


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
