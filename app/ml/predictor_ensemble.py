"""
MÃ³dulo de INFERÃŠNCIA com ENSEMBLE para a API SmartTrack.

Carrega N modelos treinados e retorna a MÃ‰DIA das previsÃµes -- essa
abordagem foi escolhida apÃ³s uma investigaÃ§Ã£o (ver
smarttrack-ml/INVESTIGACAO_BAMBU.md) que mostrou que um Ãºnico modelo
tem alta variÃ¢ncia entre rodadas de treino (68%-98% de acurÃ¡cia
dependendo sÃ³ da semente aleatÃ³ria), enquanto o ensemble reduz essa
instabilidade e melhora a precisÃ£o em casos difÃ­ceis (vegetaÃ§Ã£o de
crescimento rÃ¡pido/errÃ¡tico, como bambu).
"""

from pathlib import Path

import joblib
import numpy as np
import keras

from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent
MODEL_FILES_DIR = Path(settings.ML_MODELS_DIR)
if not MODEL_FILES_DIR.is_absolute():
    MODEL_FILES_DIR = Path.cwd() / settings.ML_MODELS_DIR

SCALER_PATH = MODEL_FILES_DIR / "scaler.joblib"

FEATURE_COLS = [
    "laser_interrompido", "duracao_interrupcao_seg_norm", "temp_c",
    "umidade_pct", "chuva_mm_mes", "radiacao_mj_m2_dia", "umidade_solo_proxy",
]


class ModeloNaoDisponivelError(Exception):
    """Levantado quando os arquivos do modelo treinado nÃ£o sÃ£o encontrados."""


class SmartTrackPredictorEnsemble:
    def __init__(self, n_modelos: int = None):
        n_modelos = n_modelos or settings.ML_N_MODELOS_ENSEMBLE

        if not SCALER_PATH.exists():
            raise ModeloNaoDisponivelError(
                f"Scaler nÃ£o encontrado em '{SCALER_PATH}'. Treine o ensemble primeiro "
                f"(ver smarttrack-ml) e copie os arquivos para '{MODEL_FILES_DIR}'."
            )

      self.modelos = []
  
      caminho = MODEL_FILES_DIR / "smarttrack_model.keras"

      if not caminho.exists():
      	raise ModeloNaoDisponivelError(
      	   f"Modelo não encontrado: '{caminho}'."
    )

self.modelos.append(keras.models.load_model(caminho))

        self.scaler = joblib.load(SCALER_PATH)

    def _preparar_features(self, janela_df) -> np.ndarray:
        df = janela_df.copy()
        df["laser_interrompido"] = (df["laser_status"] == "INTERRUPTED").astype(float)
        df["duracao_interrupcao_seg_norm"] = np.log1p(df["duracao_interrupcao_seg"]) / np.log1p(3600)

        X = df[FEATURE_COLS].values.astype(np.float32)
        n_features = X.shape[1]
        X_escalado = self.scaler.transform(X.reshape(-1, n_features)).reshape(1, 24, n_features)
        return X_escalado.astype(np.float32)

    def prever(self, janela_df) -> dict:
        if len(janela_df) != 24:
            raise ValueError(f"A janela precisa ter exatamente 24 leituras (uma por hora). Recebido: {len(janela_df)}")

        X = self._preparar_features(janela_df)

        probs, regs = [], []
        for modelo in self.modelos:
            saida = modelo.predict(X, verbose=0)
            probs.append(float(saida["classificacao_vegetacao_real"][0][0]))
            regs.append(float(saida["dias_ate_limite"][0][0]))

        prob_media = float(np.mean(probs))
        dias_media = float(np.mean(regs))

        return {
            "vegetacao_real_prob": round(prob_media, 4),
            "vegetacao_real": prob_media >= 0.5,
            "vegetacao_real_incerteza": round(float(np.std(probs)), 4),
            "dias_ate_limite_estimado": round(dias_media, 1),
            "dias_ate_limite_incerteza": round(float(np.std(regs)), 1),
        }


_predictor_instance = None
_predictor_erro = None


def get_predictor() -> SmartTrackPredictorEnsemble:
    global _predictor_instance, _predictor_erro
    if _predictor_instance is not None:
        return _predictor_instance
    if _predictor_erro is not None:
        raise _predictor_erro
    try:
        _predictor_instance = SmartTrackPredictorEnsemble()
        return _predictor_instance
    except ModeloNaoDisponivelError as e:
        _predictor_erro = e
        raise

