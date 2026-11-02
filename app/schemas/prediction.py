"""Schema Pydantic para a resposta do endpoint de predição de ML."""

from typing import Optional

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    device_id: str
    vegetacao_real_prob: float
    vegetacao_real: bool
    vegetacao_real_incerteza: float
    dias_ate_limite_estimado: float
    dias_ate_limite_incerteza: float
    janela_inicio: str
    janela_fim: str
    aviso: Optional[str] = None
