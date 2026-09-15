# Integração API ↔ Machine Learning — SmartTrack

Este documento explica, em detalhe, como o modelo de Machine Learning (desenvolvido no repositório `smarttrack-ml`) se conecta à API REST (`smarttrack-api`), quais decisões de arquitetura foram tomadas e por quê, e como manter/atualizar essa integração no futuro.

---

## 🎯 Visão geral do fluxo

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│   smarttrack-ml      │     │   smarttrack-api      │     │   Cliente (dashboard,   │
│   (repositório de     │     │   (FastAPI)            │     │   app, etc.)             │
│   treino)              │     │                        │     │                          │
│                        │     │  1. Recebe leituras     │     │                          │
│  1. Simula/carrega     │     │     (POST /readings)    │     │                          │
│     dados               │     │  2. Recebe clima        │     │                          │
│  2. Monta janelas 24h   │     │     (POST /climate-     │     │                          │
│  3. Treina ensemble      │     │     readings)            │     │                          │
│     (5 modelos)          │     │  3. Ao consultar         │     │                          │
│  4. Salva:                │     │     GET /devices/{id}/  │────▶│  Recebe JSON com:        │
│     - scaler.joblib        │────▶│     prediction:          │     │  - prob. vegetação real  │
│     - ensemble_modelo_     │copia│     - busca últimas 24h  │     │  - incerteza             │
│       0..4.keras            │(script│   - busca clima do dia │     │  - dias até o limite     │
│                              │deploy)│  - chama o ensemble   │     │  - incerteza             │
└──────────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

**Ponto-chave:** o treino (repositório `smarttrack-ml`) e a inferência (dentro da `smarttrack-api`) são **processos completamente separados**. A API nunca treina nada em tempo real — ela apenas **carrega modelos já treinados** e os usa para prever.

---

## 📂 Onde cada peça mora

| Peça | Localização | Papel |
|---|---|---|
| Pipeline de treino completo | `smarttrack-ml/ml/` | Gera os arquivos `.keras` e `scaler.joblib` |
| Script de deploy do modelo | `smarttrack-ml/deploy_model.sh` / `.ps1` | Copia os arquivos treinados até a API (com backup automático) |
| Módulo de inferência (dentro da API) | `smarttrack-api/app/ml/predictor_ensemble.py` | Carrega os modelos e expõe `.prever(janela_df)` |
| Arquivos do modelo treinado | `smarttrack-api/app/ml/model_files/` | `scaler.joblib` + `ensemble_modelo_0.keras` ... `ensemble_modelo_4.keras` |
| Endpoint HTTP | `smarttrack-api/app/routers/predictions.py` | Busca dados no banco, monta a janela, chama o predictor |
| Tabela nova no banco | `smarttrack-api/app/models/climate_reading.py` | Armazena clima diário por dispositivo |
| Coluna nova no banco | `smarttrack-api/app/models/reading.py` (`duracao_interrupcao_seg`) | Necessária como feature do modelo |

---

## 🔧 Passo a passo: como levar um modelo treinado até a API

### 1. Treine (ou retreine) o ensemble no repositório `smarttrack-ml`
```bash
cd smarttrack-ml/ml
python simulate_synthetic_fallback.py   # ou seu script com dados reais
python simulate_laser_readings.py
python feature_engineering.py
python train_ensemble.py 5
```

### 2. Rode o script de deploy (recomendado -- automatiza cópia + backup)
```bash
cd smarttrack-ml
./deploy_model.sh                        # Linux/Mac/WSL
# .\deploy_model.ps1                     # Windows PowerShell
```
Isso copia `scaler.joblib` + `ensemble_modelo_0..4.keras` para `smarttrack-api/app/ml/model_files/`, fazendo backup automático de qualquer modelo anterior. Ver `smarttrack-ml/DEPLOY.md` para detalhes.

### 3. Reinicie a API
```bash
cd smarttrack-api
uvicorn app.main:app --reload
```
Na primeira chamada ao endpoint `/devices/{device_id}/prediction`, os modelos são carregados (padrão *singleton* — só carrega uma vez, reutiliza depois).

---

## 🧩 Decisões de design da integração (e por quê)

### 1. Por que uma tabela `ClimateReading` separada de `Reading`?
O clima é medido em granularidade **diária**, enquanto as leituras do laser são **horárias**. Se colocássemos as colunas de clima dentro de `Reading`, o mesmo valor climático apareceria repetido em 24 linhas por dia. Com uma tabela separada, o endpoint de predição busca 1 registro de clima por data e "espalha" esse valor para as 24 horas daquele dia.

### 2. Por que `duracao_interrupcao_seg` é opcional (`nullable=True`) em `Reading`?
Para manter **compatibilidade retroativa**: dispositivos com firmware mais antigo continuam funcionando normalmente na regra determinística (`/devices/{id}/status`). Apenas o endpoint de predição depende desse campo, e ele já tem um valor padrão (`0.0`) quando ausente.

### 3. Por que o endpoint retorna um campo `aviso`?
Se faltar o registro climático de algum dia dentro da janela de 24h, a API **não falha** — usa valores climáticos neutros/genéricos e avisa explicitamente através do campo `aviso`. Prioriza disponibilidade sobre falha total, mas é transparente sobre a possível perda de precisão.

### 4. Por que o modelo é carregado como *singleton*?
Carregar 5 modelos Keras do disco leva de 1 a 3 segundos. Fazer isso a cada requisição tornaria a API lenta. O padrão *singleton* (`get_predictor()`) garante que os modelos sejam carregados **uma única vez**.

### 5. Por que retornar erro `503` (não `500`) quando o modelo não está disponível?
`503 Service Unavailable` comunica que **o problema é temporário e conhecido** (faltam os arquivos do modelo, corrigível copiando os arquivos certos), diferente de um `500`, que sugeriria um bug inesperado.

---

## ✅ Validação real feita nesta sessão (não apenas escrita teórica)

Antes desta entrega, eu:
1. Recebi o CSV real (`fernao_dias_vegetacao_clima_crescimento_1ano.csv`) e o processei com `load_real_climate.py`.
2. Treinei um ensemble real de 5 modelos com esses dados reais: **92.7% de acurácia, 100% recall na classe "Ruído", MAE de 4.59 dias, R² de 0.925**.
3. Rodei `deploy_model.sh` de verdade, copiando os arquivos para `app/ml/model_files/` — com **backup automático** do modelo anterior (treinado com dados sintéticos) antes da substituição.
4. Rodei os **14 testes automatizados da API** com o modelo real presente — todos passaram, incluindo a predição de ponta a ponta.
5. Subi o servidor via `uvicorn` e testei manualmente com `curl` em dois cenários opostos: interrupções longas (zona do bambu) → 99.97% de probabilidade de vegetação real; sem interrupções → 6.8%, corretamente classificado como normal.

---

## ⚠️ Limitações conhecidas desta integração (transparência)

1. **Clima "normal mensal", não leitura diária real:** conforme os metadados do próprio CSV fornecido, os valores climáticos são estimativas mensais por classificação climática (Köppen), não medições diárias de estação real (o arquivo original recomenda substituir por INMET/NASA POWER quando possível).
2. **Sem dados reais de interrupção do laser:** as interrupções (vegetação real vs. ruído) são **simuladas probabilisticamente**, não medidas em campo -- esse é o principal ponto a evoluir quando houver hardware real coletando dados.
3. **Sem preenchimento automático de `climate-readings`:** hoje é necessário popular essa tabela manualmente. Uma melhoria natural é automatizar isso com um job agendado consultando uma fonte real (INMET, NASA POWER).
4. **Ensemble de 5 modelos aumenta o tempo de resposta:** cada predição chama 5 modelos em sequência. Para volumes muito altos, considere paralelizar ou avaliar se 3 modelos já entregam estabilidade suficiente.

---

## 🚀 Próximos passos para evoluir a integração

- [ ] Job agendado (ex: `APScheduler` ou cron) para popular `climate-readings` automaticamente.
- [ ] Versionar os modelos (ex: `model_files/v1/`, `model_files/v2/`) para permitir rollback fácil entre versões (além do backup automático já feito pelo script de deploy).
- [ ] Expor a métrica de incerteza do ensemble em um dashboard de monitoramento, para acompanhar se o modelo está "confuso" com mais frequência ao longo do tempo (sinal de drift).
