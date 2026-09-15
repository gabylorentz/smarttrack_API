# SmartTrack API

API REST para o projeto **SmartTrack** — monitoramento automatizado da altura da vegetação nas margens de rodovias, usando sensores de laser (ESP32 + LoRa), agora com **predição por Machine Learning** (ensemble de redes neurais).

> 🔌 Para detalhes específicos de como a API se conecta ao modelo de ML, veja **[README_INTEGRACAO.md](./README_INTEGRACAO.md)**.

---

## ✅ Estado desta entrega

Nesta sessão, o modelo foi **retreinado com os dados REAIS da Rodovia Fernão Dias** (fornecidos pelo usuário) e integrado nesta API:
- Ensemble retreinado com o CSV real: **92.7% de acurácia**, **100% de recall na classe "Ruído"**, **MAE de 4.59 dias**, **R² de 0.925**.
- 14/14 testes automatizados passando (incluindo predição real com o ensemble retreinado).
- Servidor real subido via `uvicorn`, testado com `curl` em dois cenários: (1) interrupções longas simulando vegetação real (bambu) → 99.97% de probabilidade correta; (2) sem interrupções → 6.8% de probabilidade, corretamente classificado como ruído/normal.
- Script de deploy (`smarttrack-ml/deploy_model.sh`) executado de verdade, com **backup automático** do modelo anterior antes da substituição.

---

## 📌 Descrição do SmartTrack

O SmartTrack automatiza o monitoramento da vegetação em margens de rodovias, usando dispositivos com sensores de laser instalados em pontos estratégicos. Um emissor (KY-008) e um receptor, nas duas margens, detectam quando a vegetação interrompe o feixe — sinal de que ela pode ter atingido a altura limite.

Além da regra determinística original (`laser_status → vegetation_status`), esta versão adiciona uma camada de **inteligência preditiva**: um ensemble de redes neurais que estima (1) se uma interrupção é realmente vegetação ou apenas ruído, e (2) em quantos dias a vegetação deve atingir o limite — permitindo manutenção preventiva.

## 🏗️ Arquitetura

```
VEGETAÇÃO → KY-008 → RECEPTOR → ESP32 → LoRa → GATEWAY → API REST → BANCO → DASHBOARD
                                                              │
                                                              ├── Regra determinística (imediata)
                                                              └── Ensemble de ML (preditiva)
```

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.12+ / FastAPI | API REST |
| SQLAlchemy / SQLite | Persistência |
| TensorFlow / Keras | Ensemble de redes neurais (LSTM) |
| scikit-learn / joblib | Normalização de features |
| pytest | Testes automatizados |
| Docker | Containerização |

## 📁 Estrutura do projeto

```
smarttrack-api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/          # device.py, reading.py, climate_reading.py
│   ├── schemas/          # device.py, reading.py, climate.py, prediction.py
│   ├── routers/           # health, devices, readings, climate, predictions
│   ├── services/          # vegetation.py (regra determinística)
│   ├── ml/                 # integração com o ensemble de ML
│   │   ├── predictor_ensemble.py
│   │   └── model_files/     # scaler.joblib + ensemble_modelo_0..4.keras
│   └── core/                # config.py, enums.py
├── tests/
├── requirements.txt
├── .env.example
├── Dockerfile
├── README.md                 # este arquivo
└── README_INTEGRACAO.md       # detalhes da integração API <-> ML
```

## ⚙️ Instalação

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\Activate.ps1     # Windows
pip install -r requirements.txt
cp .env.example .env
```

⚠️ **Atenção:** `requirements.txt` inclui `tensorflow-cpu`, uma instalação pesada (vários minutos), necessária para o endpoint de predição.

## ▶️ Execução

```bash
uvicorn app.main:app --reload
```

Acesse a documentação interativa em **http://127.0.0.1:8000/docs**.

## 🌐 Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/devices` | Cadastra um dispositivo |
| GET | `/devices` | Lista dispositivos |
| GET | `/devices/{device_id}` | Consulta um dispositivo |
| GET | `/devices/{device_id}/status` | Situação atual (regra determinística) |
| POST | `/readings` | Registra uma leitura do laser |
| GET | `/readings` | Lista leituras |
| GET | `/readings/{device_id}` | Histórico de um dispositivo |
| POST | `/climate-readings` | Cadastra dado climático diário |
| GET | `/climate-readings/{device_id}` | Histórico climático |
| GET | `/devices/{device_id}/prediction` | Predição via ensemble de ML |

## 📨 Exemplo de uso completo (regra + ML)

```bash
# 1. Cadastrar dispositivo
curl -X POST http://127.0.0.1:8000/devices -H "Content-Type: application/json" -d '{
  "device_id": "ST001", "name": "Sensor KM 45", "location": "BR-101, KM 45",
  "latitude": -23.5505, "longitude": -46.6333
}'

# 2. Cadastrar dado climático do dia
curl -X POST http://127.0.0.1:8000/climate-readings -H "Content-Type: application/json" -d '{
  "device_id": "ST001", "date": "2026-09-12", "temp_c": 24, "umidade_pct": 75,
  "chuva_mm_mes": 150, "radiacao_mj_m2_dia": 16, "umidade_solo_proxy": 0.3
}'

# 3. Enviar 24 leituras horárias (uma por hora do mesmo dia)
curl -X POST http://127.0.0.1:8000/readings -H "Content-Type: application/json" -d '{
  "device_id": "ST001", "timestamp": "2026-09-12T14:00:00",
  "laser_status": "INTERRUPTED", "height_limit_cm": 15, "duracao_interrupcao_seg": 1800
}'
# ... repetir para as outras 23 horas

# 4. Consultar a predição de ML
curl http://127.0.0.1:8000/devices/ST001/prediction
```

**Resposta real obtida no teste desta sessão** (cenário: 24h de interrupções longas, simulando vegetação real na zona do bambu, com o modelo retreinado com dados reais):
```json
{
  "device_id": "ST_BAMBU",
  "vegetacao_real_prob": 0.9997,
  "vegetacao_real": true,
  "vegetacao_real_incerteza": 0.0002,
  "dias_ate_limite_estimado": 0.3,
  "dias_ate_limite_incerteza": 0.5,
  "janela_inicio": "2026-09-12 00:00:00",
  "janela_fim": "2026-09-12 23:00:00",
  "aviso": null
}
```

**Cenário oposto (sem interrupções)** — testado também nesta sessão:
```json
{
  "device_id": "ST_NORMAL",
  "vegetacao_real_prob": 0.0683,
  "vegetacao_real": false,
  "dias_ate_limite_estimado": 24.7,
  "dias_ate_limite_incerteza": 3.0
}
```

## ✅ Como executar os testes

```bash
pytest tests/ -v
```

Inclui testes de: health check, cadastro (com sucesso/duplicado/inexistente), leituras (com/sem duração), dados climáticos (CRUD), e o endpoint de predição (histórico insuficiente, dispositivo inexistente, e uma predição real com o modelo).

## 🐳 Docker

```bash
docker build -t smarttrack-api .
docker run -d -p 8000:8000 --name smarttrack-api smarttrack-api
```

⚠️ Certifique-se de que `app/ml/model_files/` contém os arquivos do modelo **antes** de construir a imagem.

## 🚀 Próximos passos

- [ ] Retreinar o ensemble com dados reais de campo (ver `README_INTEGRACAO.md` e `smarttrack-ml/README.md`).
- [ ] Adicionar autenticação (API Key) para os endpoints de escrita.
- [ ] Job agendado para popular `climate-readings` automaticamente (INMET/NASA POWER).
- [ ] Monitorar a métrica de incerteza do ensemble em produção (alerta se aumentar muito).
