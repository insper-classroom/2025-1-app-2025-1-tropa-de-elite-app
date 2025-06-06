import os
import io
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List

import joblib
import boto3
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Importa o pipeline completo
from data_processing import process_pipeline  


# ==============================================================================
#  CONFIGURAÇÃO INICIAL
# ==============================================================================
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

S3_BUCKET            = os.getenv("S3_BUCKET")
S3_KEY_MODEL         = os.getenv("S3_KEY_MODEL")
S3_KEY_PAYERS        = os.getenv("S3_KEY_PAYERS")
S3_KEY_SELLERS       = os.getenv("S3_KEY_SELLERS")
S3_KEY_TRANSACTIONAL = os.getenv("S3_KEY_TRANSACTIONAL")
DATABASE_URL         = os.getenv("DATABASE_URL")

for v in (
    "S3_BUCKET",
    "S3_KEY_MODEL",
    "S3_KEY_PAYERS",
    "S3_KEY_SELLERS",
    "S3_KEY_TRANSACTIONAL",
    "DATABASE_URL",
):
    if not os.getenv(v):
        raise RuntimeError(f"Variável de ambiente '{v}' não está definida.")

TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/fraud_api"))
TMP_DIR.mkdir(parents=True, exist_ok=True)
FRAUD_THRESHOLD = 0.54

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
#  MODELO DE DADOS E SCHEMAS
# ==============================================================================
class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String, index=True, nullable=False)
    model_score = Column(Float, nullable=False)
    tx_approved = Column(Boolean, nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PredictionResult(BaseModel):
    transaction_id: str
    model_score: float
    tx_approved: bool

class BatchResponse(BaseModel):
    message: str
    transactions_processed: int


# ==============================================================================
#  ESTADO GLOBAL E LIFESPAN
# ==============================================================================
class AppState:
    model = None
    payers_path: Path = None
    sellers_path: Path = None
    transactional_path: Path = None

state = AppState()

def download_from_s3(bucket: str, key: str, local_path: Path):
    s3_client = boto3.client("s3")
    try:
        if not local_path.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Baixando '{key}' do S3...")
            s3_client.download_file(bucket, key, str(local_path))
        else:
            print(f"[INFO] Usando arquivo local cacheado: '{local_path}'.")
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar '{key}' do bucket '{bucket}': {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("[INFO] Tabelas do banco criadas/confirmadas.")

    local_model = TMP_DIR / Path(S3_KEY_MODEL).name
    local_payers = TMP_DIR / Path(S3_KEY_PAYERS).name
    local_sellers_orig = TMP_DIR / Path(S3_KEY_SELLERS).name
    local_transactional = TMP_DIR / Path(S3_KEY_TRANSACTIONAL).name

    print("[INFO] Baixando artefatos do S3...")
    download_from_s3(S3_BUCKET, S3_KEY_MODEL, local_model)
    download_from_s3(S3_BUCKET, S3_KEY_PAYERS, local_payers)
    download_from_s3(S3_BUCKET, S3_KEY_SELLERS, local_sellers_orig)
    download_from_s3(S3_BUCKET, S3_KEY_TRANSACTIONAL, local_transactional)

    df_sellers = pd.read_feather(local_sellers_orig)
    if "latitude" not in df_sellers.columns or "longitude" not in df_sellers.columns:
        df_sellers["latitude"] = df_sellers.get("latitude", np.nan)
        df_sellers["longitude"] = df_sellers.get("longitude", np.nan)
        patched_sellers = TMP_DIR / f"patched_{Path(S3_KEY_SELLERS).name}"
        df_sellers.to_feather(patched_sellers)
        state.sellers_path = patched_sellers
        print(f"[INFO] Sellers 'patchado' salvo em {patched_sellers.name}")
    else:
        state.sellers_path = local_sellers_orig
        print("[INFO] Sellers já continha lat/lon; usando conforme baixado.")

    state.payers_path = local_payers
    state.transactional_path = local_transactional
    
    print("[INFO] Carregando modelo treinado...")
    state.model = joblib.load(local_model)
    print("[INFO] Modelo carregado.")

    print("[INFO] Startup concluído. API pronta.")
    yield


# ==============================================================================
#  INSTÂNCIA DO APP E FUNÇÕES AUXILIARES
# ==============================================================================
app = FastAPI(
    title="Fraud Detection API",
    version="1.3 (Pipeline e alinhamento corrigidos)",
    lifespan=lifespan
)

def log_predictions_to_db(predictions: List[PredictionResult], db: Session):
    print(f"[BACKGROUND] Iniciando salvamento de {len(predictions)} predições.")
    try:
        db_logs = [PredictionLog(**pred.dict()) for pred in predictions]
        db.add_all(db_logs)
        db.commit()
        print(f"[BACKGROUND] {len(predictions)} predições salvas com sucesso.")
    except Exception as e:
        print(f"[BACKGROUND-ERROR] Falha ao salvar predições no banco: {e}")
        db.rollback()
    finally:
        db.close()


# ==============================================================================
#  ENDPOINT DE PREDIÇÃO
# ==============================================================================
@app.post("/predict_batch_file", response_model=BatchResponse)
async def predict_from_form(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(..., alias="file"),
):
    try:
        conteudo = await file.read()
        df_transactions = pd.read_feather(io.BytesIO(conteudo))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler o arquivo Feather: {e}")

    required_cols = {
        "is_transactional_fraud": 0, "is_fraud": 0, "tx_fraud_report_date": pd.NaT,
        "card_bin": "", "latitude": np.nan, "longitude": np.nan
    }
    for col, default in required_cols.items():
        if col not in df_transactions.columns:
            df_transactions[col] = default

    if "transaction_id" not in df_transactions.columns:
        raise HTTPException(status_code=400, detail="Coluna 'transaction_id' não encontrada no arquivo.")
    
    new_tx_ids = df_transactions["transaction_id"].tolist()
    
    tx2_path = TMP_DIR / f"tx2_{uuid.uuid4().hex}.feather"
    df_transactions.to_feather(tx2_path)
    
    try:
        df_features = process_pipeline(
            state.payers_path, state.sellers_path, state.transactional_path, tx2_path
        )
    except Exception as e:
        tx2_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Erro no pipeline de features: {e}")
    finally:
        tx2_path.unlink(missing_ok=True)

    if df_features.empty:
        raise HTTPException(status_code=400, detail="Pipeline retornou DataFrame vazio.")

    df_new_features = df_features[df_features["transaction_id"].isin(new_tx_ids)].copy()
    if df_new_features.empty:
        raise HTTPException(status_code=400, detail="Nenhuma transaction_id enviada foi encontrada no resultado do pipeline.")

    df_new_features = df_new_features.set_index('transaction_id').loc[new_tx_ids].reset_index()

    X_test = df_new_features.drop(columns=["transaction_id"], errors="ignore")

    try:
        model_feature_names = state.model.feature_names_in_
        X_test = X_test[model_feature_names]
        print("[INFO] Colunas de entrada alinhadas com as esperadas pelo modelo.")
    except AttributeError:
        print("[WARN] O modelo não possui 'feature_names_in_'. Pulando alinhamento.")
    except KeyError as e:
        missing_cols = set(model_feature_names) - set(X_test.columns)
        raise HTTPException(status_code=500, detail=f"Erro de alinhamento: colunas faltando {list(missing_cols)}")

    # ================== SOLUÇÃO RÁPIDA E SUJA ==================
    # Preenche QUALQUER NaN restante com 0. Isso resolve o erro de conversão.
    X_test.fillna(0, inplace=True)
    # ==========================================================

    print("[INFO] Iniciando predição...")
    try:
        y_proba = state.model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba < FRAUD_THRESHOLD)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a predição: {e}")
    print("[INFO] Predição concluída.")

    results_to_log = [
        PredictionResult(
            transaction_id=str(tx_id),
            model_score=float(prob),
            tx_approved=bool(pred_flag),
        )
        for tx_id, prob, pred_flag in zip(new_tx_ids, y_proba, y_pred)
    ]

    background_tasks.add_task(log_predictions_to_db, results_to_log, SessionLocal())

    return BatchResponse(
        message="Predições processadas com sucesso e salvas em segundo plano.",
        transactions_processed=len(new_tx_ids),
    )