def _create_device(client, device_id="ST001"):
    return client.post("/devices", json={
        "device_id": device_id, "name": "Sensor KM 45", "location": "Rodovia BR-101, KM 45",
        "latitude": -23.5505, "longitude": -46.6333,
    })


def _climate_payload(device_id="ST001", date="2026-09-12"):
    return {
        "device_id": device_id, "date": date, "temp_c": 22.0, "umidade_pct": 78.0,
        "chuva_mm_mes": 180.0, "radiacao_mj_m2_dia": 17.0, "umidade_solo_proxy": 0.3,
    }


def test_create_climate_reading_success(client):
    _create_device(client)
    response = client.post("/climate-readings", json=_climate_payload())
    assert response.status_code == 201
    assert response.json()["temp_c"] == 22.0


def test_create_climate_reading_duplicado_mesma_data_retorna_409(client):
    _create_device(client)
    client.post("/climate-readings", json=_climate_payload())
    response = client.post("/climate-readings", json=_climate_payload())
    assert response.status_code == 409


def test_create_climate_reading_dispositivo_inexistente_retorna_404(client):
    response = client.post("/climate-readings", json=_climate_payload(device_id="ST999"))
    assert response.status_code == 404


def test_list_climate_readings(client):
    _create_device(client)
    client.post("/climate-readings", json=_climate_payload(date="2026-09-11"))
    client.post("/climate-readings", json=_climate_payload(date="2026-09-12"))
    response = client.get("/climate-readings/ST001")
    assert response.status_code == 200
    assert len(response.json()) == 2
