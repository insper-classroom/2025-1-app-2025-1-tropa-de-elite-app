import os
from pathlib import Path

BASE_DIR     = Path(__file__).resolve().parent.parent
MODELS_INDEX = BASE_DIR / "models" / "models_index.yaml"

MODEL_NAME    = os.getenv("MODEL_NAME", "dummy")
MODEL_VARIANT = os.getenv("MODEL_VARIANT", "sem_desacordo")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")
THRESHOLD     = float(os.getenv("THRESHOLD", "0.5"))

MODEL_PATH = BASE_DIR / "models" / MODEL_NAME / f"{MODEL_VARIANT}_{MODEL_VERSION}.joblib"
