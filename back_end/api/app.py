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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pathlib import Path

# --- Imports do Banco de Dados ---
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# ─── Carrega .env ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# ─── Vars de ambiente e Configuração ──────────────────────────────────────────
S3_BUCKET = os.getenv("S3_BUCKET")
S3_KEY_DATA = os.getenv("S3_KEY_DATA")
S3_KEY_MODEL = os.getenv("S3_KEY_MODEL")
S3_KEY_PAYERS = os.getenv("S3_KEY_PAYERS")
S3_KEY_SELLERS = os.getenv("S3_KEY_SELLERS")
DATABASE_URL = os.getenv("DATABASE_URL")

for v in ("S3_BUCKET", "S3_KEY_DATA", "S3_KEY_MODEL", "S3_KEY_PAYERS", "S3_KEY_SELLERS", "DATABASE_URL"):
    if not os.getenv(v):
        raise RuntimeError(f"Variável de ambiente '{v}' não está definida.")

TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/fraud_api"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

FRAUD_THRESHOLD = 0.804907749976376

# ─── Configuração do Banco de Dados (SQLAlchemy) ─────────────────────────────
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String, index=True)
    approved = Column(Boolean)
    probability_of_fraud = Column(Float)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Pydantic Models e Estado Global ──────────────────────────────────────────
class PredictionResult(BaseModel):
    transaction_id: str
    approved: bool
    probability_of_fraud: float

class BatchResponse(BaseModel):
    message: str
    transactions_processed: int

class AppState:
    model = None
    df_payers = None
    df_sellers = None
    df_card_last_tx = None

state = AppState()

# ─── Colunas do Modelo (definidas uma vez) ──────────────────────────────────
FEATURE_COLUMNS = [
    "regiao", "tx_amount", "tx_hour_of_day", "tx_dayofweek", "card_age_days", 
    "tx_time_diff_prev", "amount_card_norm_pdf", "terminal_age_days", 
    "terminal_card_reuse_ratio_prior", "shared_terminal_with_frauds_prior", 
    "card_fraud_count_last_1d", "card_nonfraud_count_last_1d", 
    "card_fraud_count_last_7d", "card_nonfraud_count_last_7d", 
    "amount_terminal_norm_pdf", "avg_speed_between_txs", "cardbin_fraud_count_last_30d"
]

# ─── Funções Auxiliares ────────────────────────────────────────────────────────
def download_from_s3(bucket: str, key: str, local_path: Path):
    s3_client = boto3.client("s3")
    try:
        if not local_path.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3_client.download_file(bucket, key, str(local_path))
            print(f"[INFO] Baixado '{key}' para '{local_path}'.")
        else:
            print(f"[INFO] Usando arquivo local cacheado: '{local_path}'.")
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar '{key}' do bucket '{bucket}': {e}")

def process_new_transactions(df_new: pd.DataFrame) -> pd.DataFrame:
    if df_new.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    df_proc = df_new.copy()
    original_index = df_proc.index # Preserva a ordem original
    
    df_proc["tx_datetime"] = pd.to_datetime(df_proc["tx_datetime"])
    df_proc.sort_values(by=["card_id", "tx_datetime"], inplace=True)
    
    intra_batch_diff = df_proc.groupby("card_id")["tx_datetime"].diff().dt.total_seconds()
    df_proc = df_proc.merge(state.df_card_last_tx, on="card_id", how="left")
    
    history_diff = (df_proc["tx_datetime"] - df_proc["last_tx_datetime_history"]).dt.total_seconds()
    final_diff_seconds = intra_batch_diff.fillna(history_diff)
    df_proc["tx_time_diff_prev"] = np.log1p(final_diff_seconds.fillna(0))
    
    df_proc["tx_amount"] = np.log1p(df_proc["tx_amount"])
    df_proc["tx_hour_of_day"] = df_proc["tx_datetime"].dt.hour
    df_proc["tx_dayofweek"] = df_proc["tx_datetime"].dt.weekday

    df_proc = df_proc.merge(state.df_payers, on="card_id", how="left")
    df_proc = df_proc.merge(state.df_sellers, on="terminal_id", how="left")

    df_proc["card_age_days"] = (df_proc["tx_datetime"] - df_proc["card_first_transaction"]).dt.days
    df_proc["terminal_age_days"] = (df_proc["tx_datetime"] - df_proc["terminal_operation_start"]).dt.days
    df_proc["card_age_days"] = df_proc["card_age_days"].fillna(0)
    df_proc["terminal_age_days"] = df_proc["terminal_age_days"].fillna(0)

    def get_region(lat):
        if pd.isna(lat): return "UNKNOWN"
        if lat > -10: return "Norte"
        if lat > -20: return "Centro-Oeste"
        return "Sudeste"
    df_proc["regiao"] = df_proc["latitude"].apply(get_region)

    placeholders = {
        "shared_terminal_with_frauds_prior": 0.0, "card_fraud_count_last_1d": 0.0,
        "card_nonfraud_count_last_1d": 0.0, "card_fraud_count_last_7d": 0.0,
        "card_nonfraud_count_last_7d": 0.0, "cardbin_fraud_count_last_30d": 0.0,
        "amount_card_norm_pdf": 0.5, "terminal_card_reuse_ratio_prior": 0.0,
        "amount_terminal_norm_pdf": 0.5, "avg_speed_between_txs": 0.0,
    }
    for col, val in placeholders.items(): df_proc[col] = val

    for col in FEATURE_COLUMNS:
        if col not in df_proc.columns:
            df_proc[col] = 0
    df_proc.fillna(0, inplace=True)
    
    return df_proc.set_index("transaction_id").loc[df_new["transaction_id"]].reset_index()[FEATURE_COLUMNS]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Verificando e criando tabela do banco de dados, se necessário...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[INFO] Tabela do banco de dados pronta.")
    except Exception as e:
        print(f"[ERROR] Falha ao conectar ou criar tabela no banco de dados: {e}")

    local_history = TMP_DIR / Path(S3_KEY_DATA).name
    local_model = TMP_DIR / Path(S3_KEY_MODEL).name
    local_payers = TMP_DIR / Path(S3_KEY_PAYERS).name
    local_sellers = TMP_DIR / Path(S3_KEY_SELLERS).name

    download_from_s3(S3_BUCKET, S3_KEY_DATA, local_history)
    download_from_s3(S3_BUCKET, S3_KEY_MODEL, local_model)
    download_from_s3(S3_BUCKET, S3_KEY_PAYERS, local_payers)
    download_from_s3(S3_BUCKET, S3_KEY_SELLERS, local_sellers)

    print("[INFO] Carregando e pré-processando dados históricos...")
    df_history = pd.read_parquet(local_history)
    df_history['tx_datetime'] = pd.to_datetime(df_history['tx_datetime'])
    last_tx = df_history.loc[df_history.groupby('card_id')['tx_datetime'].idxmax()]
    state.df_card_last_tx = last_tx[['card_id', 'tx_datetime']].rename(columns={'tx_datetime': 'last_tx_datetime_history'})
    print(f"[INFO] Pré-processamento do histórico concluído.")
    del df_history

    print("[INFO] Carregando modelo...")
    state.model = joblib.load(local_model)
    print("[INFO] Modelo carregado.")
    
    # --- CORREÇÃO: Este bloco estava faltando ---
    print("[INFO] Carregando e processando dados de payers e sellers...")
    temp_payers = pd.read_feather(local_payers)
    temp_sellers = pd.read_feather(local_sellers)
    
    if "card_hash" in temp_payers.columns and "card_id" not in temp_payers.columns:
        temp_payers["card_id"] = temp_payers["card_hash"]
    if "card_id" not in temp_payers.columns:
        raise RuntimeError("A coluna 'card_id' não foi encontrada ou criada no arquivo de payers.")
    
    temp_payers['card_first_transaction'] = pd.to_datetime(temp_payers['card_first_transaction'])
    state.df_payers = temp_payers[["card_id", "card_bin", "card_first_transaction"]]

    if "terminal_id" not in temp_sellers.columns:
         raise RuntimeError("A coluna 'terminal_id' não foi encontrada no arquivo de sellers.")
    temp_sellers['terminal_operation_start'] = pd.to_datetime(temp_sellers['terminal_operation_start'])
    state.df_sellers = temp_sellers[["terminal_id", "latitude", "longitude", "terminal_operation_start", "terminal_soft_descriptor"]]
    print("[INFO] Payers e Sellers carregados e processados.")
    # --- FIM DA CORREÇÃO ---
    
    print("[INFO] API pronta para receber requisições.")
    yield
    print("[INFO] Recursos liberados.")

def log_predictions_to_db(predictions: List[PredictionResult], db: Session):
    print(f"[BACKGROUND] Iniciando salvamento de {len(predictions)} predições no banco de dados.")
    try:
        db_logs = [PredictionLog(**p.model_dump()) for p in predictions]
        db.add_all(db_logs)
        db.commit()
        print(f"[BACKGROUND] {len(predictions)} predições salvas com sucesso.")
    except Exception as e:
        print(f"[BACKGROUND-ERROR] Falha ao salvar predições no banco: {e}")
        db.rollback()
    finally:
        db.close()

app = FastAPI(title="Fraud Detection API", version="1.6 (Final-Corrected)", lifespan=lifespan)

@app.post("/predict_batch_file", response_model=BatchResponse)
async def predict_from_file(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".feather"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie um arquivo no formato .feather")

    try:
        content = await file.read()
        df_new = pd.read_feather(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler o arquivo .feather: {e}")

    required = {"transaction_id", "tx_datetime", "tx_amount", "card_id", "terminal_id"}
    if not required.issubset(df_new.columns):
        missing = required - set(df_new.columns)
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes no arquivo: {missing}")
    
    # Preservar a ordem original dos transaction_ids
    original_tx_ids = df_new["transaction_id"]
    df_features = process_new_transactions(df_new)
    
    probabilities = state.model.predict_proba(df_features)[:, 1]
    is_fraud = (probabilities >= FRAUD_THRESHOLD)

    results_to_log = [
        PredictionResult(
            transaction_id=str(tx_id),
            approved=not fraud_flag,
            probability_of_fraud=float(prob)
        )
        for tx_id, fraud_flag, prob in zip(original_tx_ids, is_fraud, probabilities)
    ]

    background_tasks.add_task(log_predictions_to_db, results_to_log, db)

    return BatchResponse(
        message="Predições estão sendo processadas e salvas em segundo plano.",
        transactions_processed=len(df_new)
    )