"""
Aplicação principal FastAPI para o backend de detecção de fraudes.
"""
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa o logger
logger.add(
    "logs/api.log", 
    rotation="500 MB", 
    retention="10 days", 
    level="INFO"
)

# Configura a aplicação FastAPI
app = FastAPI(
    title="Fraud Detection API",
    description="API para detecção de fraudes em transações",
    version="1.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, deve ser mais restritivo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importa os routers após a configuração da aplicação
from api.routes.model import router as model_router
from api.routes.transaction import router as transaction_router
from api.routes.prediction import router as prediction_router
from api.routes.logs import router as logs_router

# Adiciona os routers à aplicação
app.include_router(model_router, prefix="/api/models", tags=["Models"])
app.include_router(transaction_router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(prediction_router, prefix="/api/predict", tags=["Predictions"])
app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {"message": "Fraud Detection API", "version": "1.0.0"}

@app.get("/healthcheck")
async def healthcheck():
    """Endpoint para verificar a saúde da API"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Porta configurável via variável de ambiente
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
