"""Configurações gerais da aplicação (variáveis de ambiente)."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "SmartTrack API")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smarttrack.db")

    ML_MODELS_DIR: str = os.getenv("ML_MODELS_DIR", "app/ml/model_files")
    ML_N_MODELOS_ENSEMBLE: int = int(os.getenv("ML_N_MODELOS_ENSEMBLE", "5"))


settings = Settings()
