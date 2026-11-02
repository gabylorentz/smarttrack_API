# SmartTrack API

API REST do projeto **SmartTrack**, voltada ao monitoramento da vegetação nas margens de rodovias por meio de sensores conectados ao ESP32. A API registra dispositivos, leituras do laser e dados climáticos, além de disponibilizar uma predição por Machine Learning.

> Estado atual: a API está configurada para utilizar **um modelo Keras treinado** (`smarttrack_model.keras`) e um normalizador (`scaler.joblib`). Esta versão não utiliza ensemble de cinco modelos.

## Visão geral

O SmartTrack reúne:

- cadastro e consulta de dispositivos;
- leituras horárias do sensor de laser;
- dados climáticos diários;
- regra determinística para o estado atual;
- predição de vegetação real e estimativa de dias até o limite;
- documentação interativa via Swagger.

## Arquitetura

```text
VEGETAÇÃO -> SENSOR -> ESP32 -> API REST -> BANCO -> APP/DASHBOARD
                                      |
                                      +-> Regra determinística
                                      +-> Modelo de Machine Learning
```

## Tecnologias

- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- TensorFlow / Keras
- scikit-learn / joblib
- pandas / NumPy
- pytest

## Estrutura principal

```text
smarttrack_API-main/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── core/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── ml/
│       ├── predictor_ensemble.py
│       └── model_files/
│           ├── scaler.joblib
│           └── smarttrack_model.keras
├── tests/
├── requirements.txt
├── README.md
└── README_INTEGRACAO.md
```

## Instalação no Windows PowerShell

Na raiz da API:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Arquivos obrigatórios do modelo

Antes de iniciar a API, confirme:

```powershell
Test-Path .\app\ml\model_files\scaler.joblib
Test-Path .\app\ml\model_files\smarttrack_model.keras
```

Os dois comandos devem retornar `True`.

## Execução

```powershell
uvicorn app.main:app --reload
```

Documentação interativa:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica a disponibilidade da API |
| POST | `/devices` | Cadastra um dispositivo |
| GET | `/devices` | Lista dispositivos |
| GET | `/devices/{device_id}` | Consulta um dispositivo |
| GET | `/devices/{device_id}/status` | Retorna a situação atual |
| POST | `/readings` | Registra uma leitura do laser |
| GET | `/readings` | Lista leituras |
| GET | `/readings/{device_id}` | Retorna o histórico do dispositivo |
| POST | `/climate-readings` | Cadastra um dado climático diário |
| GET | `/climate-readings/{device_id}` | Retorna o histórico climático |
| GET | `/devices/{device_id}/prediction` | Executa a predição de ML |

## Exemplo no PowerShell

### Cadastrar dispositivo

```powershell
$body = @{
    device_id = "ST001"
    name = "Sensor KM 45"
    location = "Rodovia - KM 45"
    latitude = -23.5505
    longitude = -46.6333
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/devices" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Cadastrar dado climático

```powershell
$body = @{
    device_id = "ST001"
    date = "2026-11-02"
    temp_c = 24.2
    umidade_pct = 62
    chuva_mm_mes = 82
    radiacao_mj_m2_dia = 17.8
    umidade_solo_proxy = 0.28
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/climate-readings" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Registrar leitura

O valor validado pela API nesta configuração é `INTERRUPTED`.

```powershell
$body = @{
    device_id = "ST001"
    timestamp = "2026-11-02T00:00:00"
    laser_status = "INTERRUPTED"
    height_limit_cm = 25
    duracao_interrupcao_seg = 60
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/readings" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Consultar predição

```powershell
Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/devices/ST001/prediction" `
    -Method Get |
    Format-List
```

## Testes

```powershell
pytest tests -v
```

## Observações sobre o modelo atual

- O modelo foi treinado a partir de janelas de 24 horas com sete features.
- O arquivo `scaler.joblib` precisa corresponder ao dataset usado no treinamento.
- O arquivo `smarttrack_model.keras` precisa permanecer na pasta `app/ml/model_files`.
- Como esta versão carrega um único modelo, as métricas de incerteza calculadas pelo desvio-padrão entre modelos tendem a ser `0`.
- Os dados inseridos para demonstração são sintéticos e não devem ser apresentados como medições reais de campo.

## Solução de problemas

### `ENOENT: package.json`

Esse erro pertence ao projeto do app e indica que o npm foi executado fora da pasta que contém o `package.json`.

### `Scaler não encontrado`

Confirme a existência de:

```text
app/ml/model_files/scaler.joblib
```

Depois reinicie o Uvicorn.

### `Modelo não encontrado`

Confirme a existência de:

```text
app/ml/model_files/smarttrack_model.keras
```

### `IndentationError`

Valide o arquivo antes de subir a API:

```powershell
python -m py_compile .\app\ml\predictor_ensemble.py
```

Se o comando não imprimir nada, a sintaxe está válida.
