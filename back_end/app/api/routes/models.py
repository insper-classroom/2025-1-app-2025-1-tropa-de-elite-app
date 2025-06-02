# back_end/app/api/routes/models.py
import os
import yaml
from fastapi import APIRouter
from pathlib import Path

router = APIRouter()

MODELS_INDEX = Path(__file__).resolve().parents[3] / "models" / "models_index.yaml"

@router.get("/status")
def verificar_status():
    """Endpoint simples para verificar se a API está online."""
    return {"status": "online", "message": "API está funcionando normalmente"}

@router.get("/modelos")
def listar_modelos():
    modelos = []
    with open(MODELS_INDEX, "r") as f:
        index = yaml.safe_load(f)
    for nome, variantes in index["models"].items():
        for variante, versoes in variantes.items():
            for versao in versoes:
                modelos.append({
                    "nome": nome,
                    "variante": variante,
                    "versao": versao,
                    "label": f"{nome} - {variante} - {versao}"
                })
    return modelos