"""Ponto de entrada da aplicação FastAPI -- SmartTrack API."""

from fastapi import FastAPI

from app.database import Base, engine
from app.core.config import settings
from app.routers import health, devices, readings, climate, predictions

from app.models import device as _device_model  # noqa: F401
from app.models import reading as _reading_model  # noqa: F401
from app.models import climate_reading as _climate_model  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API REST para o projeto SmartTrack -- monitoramento da altura da vegetação "
        "nas margens de rodovias via sensores de laser (ESP32 + LoRa), com predição "
        "por Machine Learning (ensemble de redes neurais)."
    ),
    version="2.0.0",
)

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(readings.router)
app.include_router(climate.router)
app.include_router(predictions.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "SmartTrack API está no ar. Acesse /docs para a documentação interativa."}
