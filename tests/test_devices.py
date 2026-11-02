def _device_payload(device_id="ST001"):
    return {
        "device_id": device_id, "name": "Sensor KM 45", "location": "Rodovia BR-101, KM 45",
        "latitude": -23.5505, "longitude": -46.6333,
    }


def test_create_device_success(client):
    response = client.post("/devices", json=_device_payload())
    assert response.status_code == 201
    assert response.json()["device_id"] == "ST001"


def test_create_device_duplicado_retorna_409(client):
    client.post("/devices", json=_device_payload())
    response = client.post("/devices", json=_device_payload())
    assert response.status_code == 409


def test_get_device_inexistente_retorna_404(client):
    response = client.get("/devices/ST999")
    assert response.status_code == 404
