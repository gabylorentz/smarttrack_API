"""
Modelo (tabela) Reading -- leitura individual enviada por um dispositivo.

NOTA DE INTEGRAÇÃO COM ML: o campo `duracao_interrupcao_seg` foi
adicionado especificamente para alimentar o modelo de Machine Learning
(ver app/ml/predictor_ensemble.py), que usa a duração da interrupção
para diferenciar "vegetação real" (interrupções longas) de "ruído"
(interrupções curtas causadas por poeira, chuva forte ou animais).

É OPCIONAL (nullable) para manter compatibilidade com dispositivos/
firmwares mais antigos que ainda não enviam essa informação.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database import Base


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    laser_status = Column(String, nullable=False)
    vegetation_status = Column(String, nullable=False)
    height_limit_cm = Column(Integer, nullable=False)

    duracao_interrupcao_seg = Column(Float, nullable=True, default=0.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    device = relationship("Device", back_populates="readings")
