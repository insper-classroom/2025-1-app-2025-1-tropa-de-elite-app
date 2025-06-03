"""
Router para endpoints relacionados a transações.
"""
from fastapi import APIRouter, Depends, HTTPException
from utils.data_handler import DataHandler
from api.schemas import Transaction
import os
from loguru import logger

router = APIRouter()

# Inicializa o handler de dados
data_handler = DataHandler(
    data_dir=os.path.join("data"),
    dvc_repo_path=os.environ.get("DVC_REPO_PATH", "../2025-1-tropa-de-elite")
)

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str):
    """
    Endpoint para obter uma transação pelo ID.
    
    Args:
        transaction_id: ID da transação
    
    Returns:
        Detalhes da transação
    """
    transaction = data_handler.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transação {transaction_id} não encontrada")
    return transaction

@router.get("/", response_model=list[Transaction])
async def get_transactions(limit: int = 100):
    """
    Endpoint para obter uma lista de transações.
    
    Args:
        limit: Limite de resultados
    
    Returns:
        Lista de transações
    """
    return data_handler.get_transactions(limit)

@router.get("/sample/load", response_model=list[Transaction])
async def load_dataset_sample(limit: int = 100):
    """
    Endpoint para carregar uma amostra do dataset.
    
    Args:
        limit: Limite de resultados
    
    Returns:
        Lista de transações carregadas
    """
    try:
        transactions = data_handler.load_dataset_sample(limit)
        return transactions
    except Exception as e:
        logger.exception(f"Erro ao carregar amostra do dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
