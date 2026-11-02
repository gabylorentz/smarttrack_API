"""
Endpoint de predição via Machine Learning (ensemble de redes neurais).

Fluxo do endpoint GET /devices/{device_id}/prediction:
    1. Busca o dispositivo pelo device_id.
    2. Busca as últimas 24 leituras (readings) do dispositivo.
    3. Para cada leitura, busca o registro climático (ClimateReading)
       correspondente à DATA daquela leitura.
    4. Monta um DataFrame no formato esperado pelo predictor.
    5. Chama o ensemble de modelos e retorna o resultado formatado.
"""

from datetime import date as date_type

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.reading import Reading
from app.models.climate_reading import ClimateReading
from app.schemas.prediction import PredictionResponse
from app.ml.predictor_ensemble import get_predictor, ModeloNaoDisponivelError

router = APIRouter(tags=["ML Predictions"])


def _buscar_climate_reading(db: Session, device_pk: int, dia: date_type):
    return (
        db.query(ClimateReading)
        .filter(ClimateReading.device_id == device_pk, ClimateReading.date == dia)
        .first()
    )


@router.get("/devices/{device_id}/prediction", response_model=PredictionResponse)
def prever_situacao_dispositivo(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispositivo '{device_id}' não encontrado")

    ultimas_leituras = (
        db.query(Reading)
        .filter(Reading.device_id == device.id)
        .order_by(Reading.timestamp.desc())
        .limit(24)
        .all()
    )

    if len(ultimas_leituras) < 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Ainda não há 24 leituras registradas para '{device_id}' "
                f"(encontradas: {len(ultimas_leituras)}). É necessário pelo menos "
                "24h de histórico (uma leitura por hora) para gerar uma predição."
            ),
        )

    ultimas_leituras = list(reversed(ultimas_leituras))

    linhas = []
    dias_sem_clima = set()
    for r in ultimas_leituras:
        dia = r.timestamp.date()
        clima = _buscar_climate_reading(db, device.id, dia)
        if clima is None:
            dias_sem_clima.add(str(dia))
            temp_c, umidade_pct, chuva_mm_mes, radiacao_mj_m2_dia, umidade_solo_proxy = 22.0, 70.0, 100.0, 15.0, 0.25
        else:
            temp_c = clima.temp_c
            umidade_pct = clima.umidade_pct
            chuva_mm_mes = clima.chuva_mm_mes
            radiacao_mj_m2_dia = clima.radiacao_mj_m2_dia
            umidade_solo_proxy = clima.umidade_solo_proxy

        linhas.append({
            "timestamp": r.timestamp, "laser_status": r.laser_status,
            "duracao_interrupcao_seg": r.duracao_interrupcao_seg or 0.0,
            "temp_c": temp_c, "umidade_pct": umidade_pct, "chuva_mm_mes": chuva_mm_mes,
            "radiacao_mj_m2_dia": radiacao_mj_m2_dia, "umidade_solo_proxy": umidade_solo_proxy,
        })

    janela_df = pd.DataFrame(linhas)

    try:
        predictor = get_predictor()
    except ModeloNaoDisponivelError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"O modelo de Machine Learning ainda não está disponível nesta API. Detalhe técnico: {e}",
        )

    resultado = predictor.prever(janela_df)

    aviso = None
    if dias_sem_clima:
        aviso = (
            f"Atenção: não havia dados climáticos cadastrados para {len(dias_sem_clima)} "
            f"dia(s) desta janela ({', '.join(sorted(dias_sem_clima))}). Foram usados valores "
            "climáticos neutros/genéricos para esses dias, o que pode reduzir a precisão da predição."
        )

    return PredictionResponse(
        device_id=device_id,
        vegetacao_real_prob=resultado["vegetacao_real_prob"],
        vegetacao_real=resultado["vegetacao_real"],
        vegetacao_real_incerteza=resultado["vegetacao_real_incerteza"],
        dias_ate_limite_estimado=resultado["dias_ate_limite_estimado"],
        dias_ate_limite_incerteza=resultado["dias_ate_limite_incerteza"],
        janela_inicio=str(ultimas_leituras[0].timestamp),
        janela_fim=str(ultimas_leituras[-1].timestamp),
        aviso=aviso,
    )
