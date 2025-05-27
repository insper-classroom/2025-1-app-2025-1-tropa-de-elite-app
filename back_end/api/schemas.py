"""
Esquemas (schemas) de dados para a API de detecção de fraudes.
"""
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field

class Transaction(BaseModel):
    """Modelo para representar uma transação."""
    id: str = Field(..., description="ID único da transação")
    timestamp: str = Field(..., description="Data e hora da transação")
    amount: float = Field(..., description="Valor da transação")
    merchantId: str = Field(..., description="ID do comerciante/terminal")
    customerId: str = Field(..., description="ID do cliente/cartão")
    cardType: Optional[str] = Field(None, description="Tipo de cartão")
    ipAddress: Optional[str] = Field(None, description="Endereço IP")
    deviceId: Optional[str] = Field(None, description="ID do dispositivo")
    location: Optional[str] = Field(None, description="Localização")
    browser: Optional[str] = Field(None, description="Navegador utilizado")
    os: Optional[str] = Field(None, description="Sistema operacional")
    transactionType: Optional[str] = Field(None, description="Tipo de transação (mobile, online, etc)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "TX-12345",
                "timestamp": "2023-05-15T10:30:45Z",
                "amount": 299.99,
                "merchantId": "TERM-123",
                "customerId": "CARD-456",
                "cardType": "VISA",
                "ipAddress": "192.168.1.1",
                "deviceId": "iPhone-13",
                "location": "São Paulo, Brasil",
                "browser": "Safari",
                "os": "iOS",
                "transactionType": "mobile"
            }
        }

class PredictionResult(BaseModel):
    """Modelo para representar o resultado de uma predição."""
    decision: str = Field(..., description="Decisão da predição (FRAUD ou NOT_FRAUD)")
    score: float = Field(..., description="Score da predição (probabilidade)")
    version: str = Field(..., description="Versão do modelo utilizado")
    timestamp: str = Field(..., description="Data e hora da predição")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Atributos adicionais")

class BatchJob(BaseModel):
    """Modelo para representar um job de processamento em lote."""
    jobId: str = Field(..., description="ID único do job")
    progress: int = Field(..., description="Progresso do job (0-100)")
    status: str = Field(..., description="Status do job (pending, processing, completed, failed)")
    downloadUrl: Optional[str] = Field(None, description="URL para download dos resultados")
    timestamp: str = Field(..., description="Data e hora de criação do job")
    userId: str = Field(..., description="ID do usuário que criou o job")

class LogEntry(BaseModel):
    """Modelo para representar um registro de log."""
    id: str = Field(..., description="ID único do log")
    timestamp: str = Field(..., description="Data e hora do log")
    transactionId: str = Field(..., description="ID da transação")
    userId: str = Field(..., description="ID do usuário")
    score: float = Field(..., description="Score da predição")
    decision: str = Field(..., description="Decisão da predição (FRAUD ou NOT_FRAUD)")
    version: str = Field(..., description="Versão do modelo utilizado")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Atributos adicionais")

class ModelInfo(BaseModel):
    """Modelo para representar informações sobre o modelo."""
    version: str = Field(..., description="Versão do modelo")
    dvcVersion: Optional[str] = Field(None, description="Versão DVC")
    modelPath: Optional[str] = Field(None, description="Caminho do modelo")
    lastUpdated: Optional[str] = Field(None, description="Data da última atualização")
    metrics: Optional[Dict[str, float]] = Field(None, description="Métricas do modelo")

class LogsFilter(BaseModel):
    """Modelo para representar filtros para logs."""
    startDate: Optional[datetime] = Field(None, description="Data de início")
    endDate: Optional[datetime] = Field(None, description="Data de fim")
    modelVersion: Optional[str] = Field(None, description="Versão do modelo")
    fraudOnly: Optional[bool] = Field(None, description="Apenas fraudes")
