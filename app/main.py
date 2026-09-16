""Ponto de entrada da aplicação FastAPI -- SmartTrack API."""
2
 
3
from fastapi import FastAPI
4
from fastapi.middleware.cors import CORSMiddleware
5
 
6
from app.database import Base, engine
7
from app.core.config import settings
8
from app.routers import health, devices, readings, climate, predictions
9
 
10
from app.models import device as _device_model # noqa: F401
11
from app.models import reading as _reading_model # noqa: F401
12
from app.models import climate_reading as _climate_model # noqa: F401
13
 
14
Base.metadata.create_all(bind=engine)
15
 
16
app = FastAPI(
17
title=settings.APP_NAME,
18
description=(
19
"API REST para o projeto SmartTrack -- monitoramento da altura da vegetação "
20
"nas margens de rodovias via sensores de laser (ESP32 + LoRa), com predição "
21
"por Machine Learning (ensemble de redes neurais)."
22
),
23
version="2.0.0",
24
)
25
 
26
# Libera o acesso via navegador/app para o app React Native (CORS).
27
app.add_middleware(
28
CORSMiddleware,
29
allow_origins=["*"], # ⚠️ ajuste para produção no futuro
30
allow_credentials=True,
31
allow_methods=["*"],
32
allow_headers=["*"],
33
)
34
 
35
app.include_router(health.router)
36
app.include_router(devices.router)
37
app.include_router(readings.router)
38
app.include_router(climate.router)
39
app.include_router(predictions.router)
40
 
41
 
42
@app.get("/", tags=["Health"])
43
def root():
44
return {"message": "SmartTrack API está no ar. Acesse /docs para a documentação interativa."}
