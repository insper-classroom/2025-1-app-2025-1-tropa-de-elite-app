"""
Router para endpoints relacionados a predições.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from models.model_handler import ModelHandler
from utils.data_handler import DataHandler
from utils.log_handler import LogHandler
from utils.batch_handler import BatchJobHandler
from api.schemas import PredictionResult, BatchJob
import os
import uuid
from loguru import logger

router = APIRouter()

# Inicializa os handlers
model_handler = ModelHandler(models_dir=os.path.join("models"))
data_handler = DataHandler(
    data_dir=os.path.join("data"),
    dvc_repo_path=os.environ.get("DVC_REPO_PATH", "../2025-1-tropa-de-elite")
)
log_handler = LogHandler(db_path=os.path.join("logs", "fraud_logs.db"))
batch_handler = BatchJobHandler(jobs_dir=os.path.join("data", "batch_jobs"))

@router.get("/transaction/{transaction_id}", response_model=PredictionResult)
async def predict_transaction(transaction_id: str, user_id: str = "system"):
    """
    Endpoint para prever fraude em uma transação.
    
    Args:
        transaction_id: ID da transação
        user_id: ID do usuário que solicitou a predição
    
    Returns:
        Resultado da predição
    """
    try:
        # Obtém a transação
        transaction = data_handler.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transação {transaction_id} não encontrada")
        
        # Faz a predição
        prediction = model_handler.predict(transaction)
        
        # Registra a predição no log
        log_handler.log_prediction(prediction, user_id)
        
        return prediction
    except Exception as e:
        logger.exception(f"Erro ao prever transação {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=dict)
async def submit_batch_job(file: UploadFile = File(...), user_id: str = Form("system")):
    """
    Endpoint para enviar um job de processamento em lote.
    
    Args:
        file: Arquivo CSV com transações para prever
        user_id: ID do usuário que enviou o job
    
    Returns:
        ID do job criado
    """
    try:
        # Salva o arquivo enviado
        file_path = os.path.join("data", "batch_uploads", f"{uuid.uuid4()}_{file.filename}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Cria o job
        job_id = batch_handler.create_job(file_path, user_id)
        
        return {"jobId": job_id}
    except Exception as e:
        logger.exception(f"Erro ao enviar job em lote: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch/{job_id}/status", response_model=BatchJob)
async def get_batch_job_status(job_id: str):
    """
    Endpoint para obter o status de um job de processamento em lote.
    
    Args:
        job_id: ID do job
    
    Returns:
        Status do job
    """
    try:
        job = batch_handler.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
        return job
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.exception(f"Erro ao obter status do job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch/{job_id}/download")
async def download_batch_results(job_id: str):
    """
    Endpoint para baixar os resultados de um job de processamento em lote.
    
    Args:
        job_id: ID do job
    
    Returns:
        Arquivo CSV com os resultados
    """
    try:
        result_path = batch_handler.get_result_path(job_id)
        if not result_path:
            raise HTTPException(status_code=404, detail=f"Resultados para o job {job_id} não encontrados")
        
        return FileResponse(
            path=result_path,
            filename=f"fraud_detection_results_{job_id}.csv",
            media_type="text/csv"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.exception(f"Erro ao baixar resultados do job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
