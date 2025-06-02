import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Configura logger para saída JSON no stdout
logger.remove()
logger.add(sys.stdout, serialize=True, level="INFO")

app = FastAPI(title="Fraud Detection API")

# Habilita CORS para o front-end em localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importa e inclui os routers
from app.api.routes.models  import router as models_router
from app.api.routes.predict import router as predict_router
from app.api.routes.data    import router as data_router

app.include_router(models_router,  prefix="/api",        tags=["models"])
app.include_router(predict_router, prefix="/api/predict", tags=["predict"])
app.include_router(data_router,     prefix="/api/data",    tags=["data"])
