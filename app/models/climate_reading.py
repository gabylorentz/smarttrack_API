"""
Modelo (tabela) ClimateReading -- registro climático DIÁRIO por
dispositivo, usado como entrada para o modelo de Machine Learning.

Tabela separada de `Reading` porque o clima é DIÁRIO e as leituras do
laser são HORÁRIAS -- misturar as granularidades geraria duplicação de
dados climáticos em 24 linhas idênticas por dia.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class ClimateReading(Base):
    __tablename__ = "climate_readings"
    __table_args__ = (
        UniqueConstraint("device_id", "date", name="uq_climate_device_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)

    temp_c = Column(Float, nullable=False)
    umidade_pct = Column(Float, nullable=False)
    chuva_mm_mes = Column(Float, nullable=False)
    radiacao_mj_m2_dia = Column(Float, nullable=False)
    umidade_solo_proxy = Column(Float, nullable=False, default=0.25)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    device = relationship("Device")
