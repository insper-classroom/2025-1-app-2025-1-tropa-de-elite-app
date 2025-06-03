"""
Router para endpoints relacionados ao modelo.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from models.model_handler import ModelHandler
from utils.dvc_handler import DVCHandler
from api.schemas import ModelInfo
import os
from loguru import logger

router = APIRouter()

# Inicializa os handlers
model_handler = ModelHandler(models_dir=os.path.join("models"))
dvc_handler = DVCHandler(dvc_repo_path=os.environ.get("DVC_REPO_PATH", "../2025-1-tropa-de-elite"))

@router.get("/current", response_model=ModelInfo)
async def get_current_model():
    """Endpoint para obter informações sobre o modelo atual."""
    try:
        # Obtém informações do modelo
        model_info = model_handler.get_model_info()
        
        # Adiciona informações do DVC
        dvc_info = dvc_handler.get_current_model_info()
        model_info.update({
            "dvcVersion": dvc_info.get("dvcVersion"),
            "modelPath": dvc_info.get("modelPath")
        })
        
        return model_info
    except Exception as e:
        logger.exception(f"Erro ao obter informações do modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/versions", response_model=list[str])
async def get_model_versions():
    """Endpoint para obter todas as versões disponíveis do modelo."""
    try:
        # Em um sistema real, você obteria isso do repositório DVC
        # Por simplicidade, retornamos versões fixas
        return ["v1.0.0", "v0.9.0", "v0.8.5"]
    except Exception as e:
        logger.exception(f"Erro ao obter versões do modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_model_metrics():
    """Endpoint para obter métricas do modelo atual."""
    try:
        model_info = model_handler.get_model_info()
        return model_info.get("metrics", {})
    except Exception as e:
        logger.exception(f"Erro ao obter métricas do modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
