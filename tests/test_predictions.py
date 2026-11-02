"""
Testes do endpoint de predição (GET /devices/{device_id}/prediction).

O teste de predição bem-sucedida é pulado automaticamente se os
arquivos do modelo não estiverem presentes em app/ml/model_files/.
"""

from pathlib import Path

import pytest

from app.core.config import settings

MODEL_FILES_DIR = Path(settings.ML_MODELS_DIR)
MODELO_DISPONIVEL = (MODEL_FILES_DIR / "scaler.joblib").exists()


def _create_device(client, device_id="ST001"):
    return client.post("/devices", json={
        "device_id": device_id, "name": "Sensor KM 45", "location": "Rodovia BR-101, KM 45",
        "latitude": -23.5505, "longitude": -46.6333,
    })


def test_prediction_dispositivo_inexistente_retorna_404(client):
    response = client.get("/devices/ST999/prediction")
    assert response.status_code == 404


def test_prediction_sem_24_leituras_retorna_400(client):
    _create_device(client)
    client.post("/readings", json={
        "device_id": "ST001", "timestamp": "2026-09-12T10:00:00",
        "laser_status": "DETECTED", "height_limit_cm": 15,
    })
    response = client.get("/devices/ST001/prediction")
    assert response.status_code == 400


@pytest.mark.skipif(not MODELO_DISPONIVEL, reason="Modelo de ML não treinado/copiado neste ambiente")
def test_prediction_com_modelo_disponivel(client):
    _create_device(client)
    client.post("/climate-readings", json={
        "device_id": "ST001", "date": "2026-09-12", "temp_c": 22.0, "umidade_pct": 78.0,
        "chuva_mm_mes": 180.0, "radiacao_mj_m2_dia": 17.0, "umidade_solo_proxy": 0.3,
    })
    for hora in range(24):
        client.post("/readings", json={
            "device_id": "ST001",
            "timestamp": f"2026-09-12T{hora:02d}:00:00",
            "laser_status": "DETECTED", "height_limit_cm": 15,
        })
    response = client.get("/devices/ST001/prediction")
    assert response.status_code == 200
    body = response.json()
    assert "vegetacao_real_prob" in body
    assert "dias_ate_limite_estimado" in body
