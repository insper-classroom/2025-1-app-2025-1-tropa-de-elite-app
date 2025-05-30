import sys
from fastapi import FastAPI
from loguru   import logger

# Logger JSON para STDOUT
logger.remove()
logger.add(sys.stdout, serialize=True, level="INFO")

app = FastAPI(title="Fraud Detection API")

# Routers
from app.api.routes.models  import router as models_router
from app.api.routes.predict import router as predict_router
from app.api.routes.data    import router as data_router

app.include_router(models_router,  prefix="/api",       tags=["models"])
app.include_router(predict_router, prefix="/api/predict",tags=["predict"])
app.include_router(data_router,     prefix="/api/data",  tags=["data"])
