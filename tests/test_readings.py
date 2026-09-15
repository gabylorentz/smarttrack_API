def _create_device(client, device_id="ST001"):
    return client.post("/devices", json={
        "device_id": device_id, "name": "Sensor KM 45", "location": "Rodovia BR-101, KM 45",
        "latitude": -23.5505, "longitude": -46.6333,
    })


def test_create_reading_calcula_vegetation_status_e_aceita_duracao(client):
    _create_device(client)
    response = client.post("/readings", json={
        "device_id": "ST001", "timestamp": "2026-09-12T20:30:00",
        "laser_status": "INTERRUPTED", "height_limit_cm": 15,
        "duracao_interrupcao_seg": 1800,
    })
    assert response.status_code == 201
    body = response.json()
    assert body["vegetation_status"] == "ABOVE_LIMIT"
    assert body["duracao_interrupcao_seg"] == 1800


def test_create_reading_sem_duracao_usa_default_zero(client):
    _create_device(client)
    response = client.post("/readings", json={
        "device_id": "ST001", "timestamp": "2026-09-12T20:30:00",
        "laser_status": "DETECTED", "height_limit_cm": 15,
    })
    assert response.status_code == 201
    assert response.json()["duracao_interrupcao_seg"] == 0.0


def test_create_reading_dispositivo_inexistente_retorna_404(client):
    response = client.post("/readings", json={
        "device_id": "ST999", "timestamp": "2026-09-12T20:30:00",
        "laser_status": "DETECTED", "height_limit_cm": 15,
    })
    assert response.status_code == 404
