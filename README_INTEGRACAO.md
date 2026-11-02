# Integração API e Machine Learning — SmartTrack

Este documento descreve a integração atualmente configurada entre o repositório de treinamento `smarttrack-ml` e a API `smarttrack_API-main`.

> Esta versão utiliza **um único modelo Keras**. O nome `predictor_ensemble.py` foi mantido por compatibilidade com a estrutura existente, mas o carregamento atual aponta para `smarttrack_model.keras`.

## Fluxo atual

```text
smarttrack-ml                                smarttrack_API-main
┌──────────────────────────┐                 ┌─────────────────────────────┐
│ leituras_simuladas.csv   │                 │ POST /readings              │
│          |               │                 │ POST /climate-readings      │
│ feature_engineering.py   │                 │          |                  │
│          |               │   copiar        │ últimas 24 leituras         │
│ dataset_processado.npz   │  ----------->   │ + clima do dia              │
│ scaler.joblib            │                 │          |                  │
│          |               │                 │ predictor_ensemble.py       │
│ train.py                 │                 │          |                  │
│          |               │                 │ smarttrack_model.keras      │
│ smarttrack_model.keras   │                 │          |                  │
└──────────────────────────┘                 │ resposta JSON               │
                                             └─────────────────────────────┘
```

## Responsabilidades

### Repositório `smarttrack-ml`

Responsável por:

1. carregar ou simular dados;
2. construir janelas de 24 horas;
3. normalizar as sete features;
4. gerar `dataset_processado.npz`;
5. gerar `scaler.joblib`;
6. treinar e salvar `smarttrack_model.keras`.

### Repositório `smarttrack_API-main`

Responsável por:

1. receber dispositivos, leituras e clima;
2. consultar as últimas 24 leituras do dispositivo;
3. montar as features na mesma ordem usada no treinamento;
4. aplicar o `scaler.joblib`;
5. carregar `smarttrack_model.keras`;
6. devolver a classificação e a estimativa de dias até o limite.

## Features esperadas

A ordem precisa ser mantida entre treinamento e inferência:

```python
FEATURE_COLS = [
    "laser_interrompido",
    "duracao_interrupcao_seg_norm",
    "temp_c",
    "umidade_pct",
    "chuva_mm_mes",
    "radiacao_mj_m2_dia",
    "umidade_solo_proxy",
]
```

A duração é normalizada antes da aplicação do scaler:

```python
df["duracao_interrupcao_seg_norm"] = (
    np.log1p(df["duracao_interrupcao_seg"]) / np.log1p(3600)
)
```

## Preparação do dataset no Windows

Na raiz de `smarttrack-ml`:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r ml_requirements.txt
python .\ml\feature_engineering.py
```

Arquivos esperados após o processamento:

```text
data/dataset_processado.npz
data/scaler.joblib
```

## Treinamento

Antes do treinamento, `ml/train.py` deve usar caminhos relativos:

```python
DATASET_PATH = "data/dataset_processado.npz"
MODELO_PATH = "data/smarttrack_model.keras"
```

Execute:

```powershell
python .\ml\train.py
```

Arquivo esperado:

```text
data/smarttrack_model.keras
```

## Publicação manual na API

Na raiz de `smarttrack-ml`:

```powershell
$destino = "C:\Users\LoGa564\Downloads\smarttrack_API-main\smarttrack_API-main\app\ml\model_files"

New-Item -ItemType Directory -Force -Path $destino | Out-Null
Copy-Item ".\data\scaler.joblib" $destino -Force
Copy-Item ".\data\smarttrack_model.keras" $destino -Force
```

Confirme:

```powershell
Test-Path "$destino\scaler.joblib"
Test-Path "$destino\smarttrack_model.keras"
```

## Configuração necessária no predictor

O carregamento do modelo deve apontar para:

```python
self.modelos = []

caminho = MODEL_FILES_DIR / "smarttrack_model.keras"

if not caminho.exists():
    raise ModeloNaoDisponivelError(
        f"Modelo não encontrado: '{caminho}'."
    )

self.modelos.append(keras.models.load_model(caminho))
self.scaler = joblib.load(SCALER_PATH)
```

O bloco acima deve permanecer dentro de `SmartTrackPredictorEnsemble.__init__`, usando espaços consistentes. Valide com:

```powershell
python -m py_compile .\app\ml\predictor_ensemble.py
```

## Reinício da API

O predictor usa uma instância em memória. Depois de trocar o modelo, o scaler ou o código, encerre o Uvicorn com `Ctrl + C` e inicie novamente:

```powershell
uvicorn app.main:app --reload
```

## Condições para a predição

A API precisa de:

- dispositivo cadastrado;
- exatamente 24 leituras para a janela usada na inferência;
- dados climáticos correspondentes;
- `scaler.joblib` disponível;
- `smarttrack_model.keras` disponível;
- compatibilidade entre as features do scaler, do modelo e da API.

## Incerteza na versão com modelo único

O código atual mantém a estrutura de lista `self.modelos` e calcula média e desvio-padrão. Com apenas um item:

- a média é a previsão do próprio modelo;
- o desvio-padrão é `0`;
- os campos de incerteza não representam variação entre treinamentos.

Para voltar a usar um ensemble real no futuro, será necessário criar um script que treine múltiplos modelos com sementes ou amostragens diferentes, salvar cada artefato e restaurar o carregamento múltiplo no predictor.

## Verificação de ponta a ponta

Com a API rodando:

```powershell
Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/devices/ST001/prediction" `
    -Method Get |
    Format-List
```

A resposta esperada contém:

```text
device_id
vegetacao_real_prob
vegetacao_real
vegetacao_real_incerteza
dias_ate_limite_estimado
dias_ate_limite_incerteza
janela_inicio
janela_fim
aviso
```

## Limitações atuais

- O modelo atual não é um ensemble de cinco redes.
- Dados usados para demonstração da API são sintéticos.
- O treinamento exibiu acurácia de classificação de `0.7630` e MAE de `2.9157` dias na execução local informada.
- A validade para uso em campo depende de validação com medições reais e monitoramento de drift.
