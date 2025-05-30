from fastapi import APIRouter
import yaml
from pathlib import Path
from app.config import MODELS_INDEX

router = APIRouter()

@router.get("/models")
def list_models():
    with open(MODELS_INDEX, 'r') as f:
        idx = yaml.safe_load(f)
    return idx["models"]
