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

# Importa o pipeline completo que agora PRESERVA `transaction_id` no DataFrame de saída
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
S3_KEY_TRANSACTIONAL = os.getenv("S3_KEY_TRANSACTIONAL")  # histórico “5 M”
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

# Diretório temporário local
TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/fraud_api"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Limiar para aprovar transação
FRAUD_THRESHOLD = 0.54

# Configuração do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
#  MODELO DE DADOS NO BANCO (PredictionLog)
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


# ==============================================================================
#  SCHEMAS Pydantic PARA TRANSFERÊNCIA DE DADOS
# ==============================================================================
class PredictionResult(BaseModel):
    transaction_id: str = Field(..., description="ID da transação processada")
    model_score: float = Field(..., description="Probabilidade de fraude (pontuação do modelo)")
    tx_approved: bool = Field(..., description="Se a transação foi aprovada pelo modelo")


class BatchResponse(BaseModel):
    message: str
    transactions_processed: int


# ==============================================================================
#  ESTADO GLOBAL DA APLICAÇÃO
# ==============================================================================
class AppState:
    model = None
    payers_path: Path = None
    sellers_path: Path = None
    transactional_path: Path = None  # histórico “5 M preprocessadas”


state = AppState()


# ==============================================================================
#  UTILITÁRIOS PARA DOWNLOAD E LIFECYCLE
# ==============================================================================
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
    """
    1) Cria a tabela prediction_logs (se ainda não existir).
    2) Baixa os Feathers de payers, sellers e transactional do S3.
    3) “Patch” em sellers: garante colunas 'latitude' e 'longitude'.
    4) Armazena em `state`:
       - payers_path
       - sellers_path (via arquivo “patched”)
       - transactional_path
    5) Carrega o modelo joblib em memória.
    """
    # 1) Garante que a tabela de logs exista
    Base.metadata.create_all(bind=engine)
    print("[INFO] Tabelas do banco criadas/confirmadas.")

    # 2) Paths locais
    local_model         = TMP_DIR / Path(S3_KEY_MODEL).name
    local_payers        = TMP_DIR / Path(S3_KEY_PAYERS).name
    local_sellers_orig  = TMP_DIR / Path(S3_KEY_SELLERS).name
    local_transactional = TMP_DIR / Path(S3_KEY_TRANSACTIONAL).name

    print("[INFO] Baixando artefatos do S3...")
    download_from_s3(S3_BUCKET, S3_KEY_MODEL, local_model)
    download_from_s3(S3_BUCKET, S3_KEY_PAYERS, local_payers)
    download_from_s3(S3_BUCKET, S3_KEY_SELLERS, local_sellers_orig)
    download_from_s3(S3_BUCKET, S3_KEY_TRANSACTIONAL, local_transactional)

    # 3) “Patch” em sellers: se não houver latitude/longitude, adiciona/reescreve
    df_sellers = pd.read_feather(local_sellers_orig)
    sobrescreveu = False

    if "latitude" not in df_sellers.columns:
        df_sellers["latitude"] = np.nan
        sobrescreveu = True
    if "longitude" not in df_sellers.columns:
        df_sellers["longitude"] = np.nan
        sobrescreveu = True

    if sobrescreveu:
        patched_sellers = TMP_DIR / f"patched_{Path(S3_KEY_SELLERS).name}"
        df_sellers.to_feather(patched_sellers)
        state.sellers_path = patched_sellers
        print(f"[INFO] Sellers “patchado” salvo em {patched_sellers.name}")
    else:
        state.sellers_path = local_sellers_orig
        print("[INFO] Sellers já continha latitude/longitude; usando conforme baixado.")

    # 4) Armazena payers e transactional no estado
    state.payers_path        = local_payers
    state.transactional_path = local_transactional

    # 5) Carrega o modelo joblib em memória
    print("[INFO] Carregando modelo treinado...")
    state.model = joblib.load(local_model)
    print("[INFO] Modelo carregado.")

    print("[INFO] Startup concluído. API pronta.")
    yield


# ==============================================================================
#  INSTÂNCIA DO APP
# ==============================================================================
app = FastAPI(
    title="Fraud Detection API",
    version="1.2 (Preserva transaction_id e filtra só body)",
    lifespan=lifespan
)


# ==============================================================================
#  FUNÇÃO PARA SALVAR PREDIÇÕES NO BANCO (background)
# ==============================================================================
def log_predictions_to_db(predictions: List[PredictionResult], db: Session):
    print(f"[BACKGROUND] Iniciando salvamento de {len(predictions)} predições no banco de dados.")
    try:
        db_logs = [
            PredictionLog(
                transaction_id=pred.transaction_id,
                model_score=pred.model_score,
                tx_approved=pred.tx_approved,
                request_timestamp=datetime.utcnow(),
            )
            for pred in predictions
        ]
        db.add_all(db_logs)
        db.commit()
        print(f"[BACKGROUND] {len(predictions)} predições salvas com sucesso.")
    except Exception as e:
        print(f"[BACKGROUND-ERROR] Falha ao salvar predições no banco: {e}")
        db.rollback()
    finally:
        db.close()


# ==============================================================================
#  ENDPOINT PARA PREDIÇÃO (Recebe Feather de transações, campo “file”)
# ==============================================================================
@app.post("/predict_batch_file", response_model=BatchResponse)
async def predict_from_form(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(..., alias="file"),
):
    """
    1. Lê o Feather de transações enviado no body (campo “file”).
    2. Garante as colunas que o pipeline espera (is_transactional_fraud, is_fraud, etc.).
    3. Salva esse DataFrame em tx2_path.
    4. tx1_path é o Feather “transactional” baixado no startup.
    5. Chama process_pipeline(payers_path, sellers_path, tx1_path, tx2_path).
    6. Filtra o DataFrame de features para manter apenas transações cujo
       `transaction_id` veio no body.
    7. Executa predição no modelo apenas nessas linhas filtradas.
    8. Salva logs e retorna BatchResponse.
    """
    # 1) Lê o Feather enviado
    try:
        conteudo = await file.read()
        df_transactions = pd.read_feather(io.BytesIO(conteudo))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler o arquivo Feather: {e}")

    # 2) Garante colunas exigidas pelo pipeline
    if "is_transactional_fraud" not in df_transactions.columns:
        df_transactions["is_transactional_fraud"] = 0
    if "is_fraud" not in df_transactions.columns:
        df_transactions["is_fraud"] = 0

    if "tx_fraud_report_date" not in df_transactions.columns:
        df_transactions["tx_fraud_report_date"] = pd.NaT
    if "card_bin" not in df_transactions.columns:
        df_transactions["card_bin"] = ""
    if "latitude" not in df_transactions.columns:
        df_transactions["latitude"] = np.nan
    if "longitude" not in df_transactions.columns:
        df_transactions["longitude"] = np.nan

    if "transaction_id" not in df_transactions.columns:
        raise HTTPException(
            status_code=400,
            detail="Coluna 'transaction_id' não encontrada no arquivo enviado em 'file'."
        )

    # 3) Guarda lista de IDs na ordem original
    new_tx_ids = df_transactions["transaction_id"].tolist()

    # 4) Grava em Feather temporário (tx2_path)
    tx2_path = TMP_DIR / f"tx2_{uuid.uuid4().hex}.feather"
    df_transactions.to_feather(tx2_path)

    # 5) Feather histórico (“5 M preprocessadas”) vem do bucket: tx1_path
    tx1_path = state.transactional_path

    # 6) Executa o pipeline completo: retorna df_features com transaction_id preservado
    try:
        df_features = process_pipeline(
            state.payers_path,
            state.sellers_path,
            tx1_path,
            tx2_path
        )
    except Exception as e:
        tx2_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Erro no pipeline de features: {e}")

    # 7) Remove Feather temporário do body
    tx2_path.unlink(missing_ok=True)

    if df_features.empty:
        raise HTTPException(status_code=400, detail="Pipeline retornou DataFrame vazio após gerar features.")

    # 8) FILTRA APENAS LINHAS NOVAS (que vieram no body)
    #    Como agora `process_pipeline` preserva transaction_id, basta:
    df_new_features = df_features[df_features["transaction_id"].isin(new_tx_ids)].copy()
    if df_new_features.empty:
        raise HTTPException(status_code=400, detail="Nenhuma das transaction_id enviadas apareceu no DataFrame de features.")

    # 9) Prepara X_test com apenas as colunas de features (drop transaction_id)
    X_test = df_new_features.drop(columns=["transaction_id"], errors="ignore")

    # 10) Tenta alinhar colunas com o que o modelo espera
    try:
        train_cols = state.model.steps[-1][1].estimators_[0].steps[-1][1].feature_name_
        X_test = X_test[train_cols]
        print("[INFO] Ordem das colunas alinhada com o modelo.")
    except Exception as e:
        print(f"[WARN] Não foi possível alinhar colunas: {e}. Usando a ordem de df_new_features.")

    # 11) Executa a predição
    print("[INFO] Iniciando predição...")
    try:
        y_proba = state.model.predict_proba(X_test)[:, 1]
        # Se probabilidade < limiar, tx_approved = True
        y_pred = (y_proba < FRAUD_THRESHOLD)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a predição: {e}")
    print("[INFO] Predição concluída.")

    # 12) Monta lista de PredictionResult (na ordem original)
    results_to_log = [
        PredictionResult(
            transaction_id=str(tx_id),
            model_score=float(prob),
            tx_approved=bool(pred_flag),
        )
        for tx_id, prob, pred_flag in zip(new_tx_ids, y_proba, y_pred)
    ]

    # 13) Salva em background no banco de dados
    background_tasks.add_task(log_predictions_to_db, results_to_log, db)

    # 14) Retorna BatchResponse
    return BatchResponse(
        message="Predições processadas com sucesso e salvas em segundo plano.",
        transactions_processed=len(new_tx_ids),
    )
