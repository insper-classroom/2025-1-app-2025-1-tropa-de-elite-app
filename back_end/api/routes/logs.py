"""
Router para endpoints relacionados a logs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from utils.log_handler import LogHandler
from api.schemas import LogEntry, LogsFilter
import os
import csv
import tempfile
from datetime import datetime
from typing import Optional, List
from loguru import logger

router = APIRouter()

# Inicializa o handler de logs
log_handler = LogHandler(db_path=os.path.join("logs", "fraud_logs.db"))

@router.get("/", response_model=List[LogEntry])
async def get_logs(
    start: Optional[datetime] = Query(None, description="Data de início"),
    end: Optional[datetime] = Query(None, description="Data de fim"),
    model: Optional[str] = Query(None, description="Versão do modelo"),
    fraudOnly: bool = Query(False, description="Apenas logs de fraude"),
    limit: int = Query(100, description="Limite de resultados")
):
    """
    Endpoint para obter logs com base em filtros.
    
    Args:
        start: Data de início
        end: Data de fim
        model: Versão do modelo
        fraudOnly: Apenas logs de fraude
        limit: Limite de resultados
    
    Returns:
        Lista de logs
    """
    try:
        logs = log_handler.get_logs(
            start_date=start,
            end_date=end,
            model_version=model,
            fraud_only=fraudOnly,
            limit=limit
        )
        return logs
    except Exception as e:
        logger.exception(f"Erro ao obter logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_logs(
    start: Optional[datetime] = Query(None, description="Data de início"),
    end: Optional[datetime] = Query(None, description="Data de fim"),
    model: Optional[str] = Query(None, description="Versão do modelo"),
    fraudOnly: bool = Query(False, description="Apenas logs de fraude"),
    limit: int = Query(1000, description="Limite de resultados")
):
    """
    Endpoint para exportar logs em formato CSV.
    
    Args:
        start: Data de início
        end: Data de fim
        model: Versão do modelo
        fraudOnly: Apenas logs de fraude
        limit: Limite de resultados
    
    Returns:
        Arquivo CSV com os logs
    """
    try:
        logs = log_handler.get_logs(
            start_date=start,
            end_date=end,
            model_version=model,
            fraud_only=fraudOnly,
            limit=limit
        )
        
        # Cria um arquivo CSV temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="") as f:
            temp_path = f.name
            writer = csv.DictWriter(f, fieldnames=[
                "id", "timestamp", "transactionId", "userId", "score", "decision", "version"
            ])
            
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    "id": log["id"],
                    "timestamp": log["timestamp"],
                    "transactionId": log["transactionId"],
                    "userId": log["userId"],
                    "score": log["score"],
                    "decision": log["decision"],
                    "version": log["version"]
                })
        
        # Retorna o arquivo CSV
        return FileResponse(
            path=temp_path,
            filename=f"fraud_detection_logs_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
            media_type="text/csv",
            background=lambda: os.unlink(temp_path)  # Remove o arquivo após o download
        )
    except Exception as e:
        logger.exception(f"Erro ao exportar logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_log_stats():
    """
    Endpoint para obter estatísticas dos logs.
    
    Returns:
        Estatísticas dos logs
    """
    try:
        # Em um sistema real, você calcularia estatísticas a partir dos logs
        # Por simplicidade, retornamos estatísticas fixas
        return {
            "totalTransactions": 1000,
            "fraudTransactions": 150,
            "fraudRate": 0.15,
            "averageScore": 0.35,
            "lastUpdate": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception(f"Erro ao obter estatísticas dos logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
